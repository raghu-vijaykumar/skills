#!/usr/bin/env node
// The CLI reads one project contract and resolves composition metadata through
// Remotion itself; source text and repository names never identify a render.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {spawn, spawnSync} from 'node:child_process';
import {parse} from 'yaml';
import {bundle} from '@remotion/bundler';
import {getCompositions} from '@remotion/renderer';
import {publishYoutube} from './publish-youtube.mjs';
import {scaffoldDraft} from './scaffold.mjs';

const toolkit = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cwd = process.cwd();
const [command, id, ...args] = process.argv.slice(2);

function die(message) { throw new Error(message); }
function run(executable, argv, label) {
  const result = spawnSync(executable, argv, {cwd, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024});
  if (result.error || result.status !== 0) {
    const lines = `${result.stdout ?? ''}\n${result.stderr ?? ''}`.trim().split(/\r?\n/).filter(Boolean);
    die(`${label}: ${result.error?.message ?? lines.slice(-10).join('\n')}`);
  }
  console.log(`${label}: passed`);
}
function flag(name) {
  const index = args.findIndex((arg) => arg === `--${name}` || arg.startsWith(`--${name}=`));
  if (index < 0) return null;
  if (args[index].includes('=')) return args[index].slice(name.length + 3);
  const value = args[index + 1];
  if (!value || value.startsWith('--')) die(`--${name} needs a value`);
  return value;
}
function hasFlag(name) { return args.includes(`--${name}`); }
function safeId(value) {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(value ?? '')) die('An ID must contain only letters, digits, and hyphens');
  return value;
}
async function project(videoId = null) {
  const configPath = path.join(cwd, 'videogen.config.ts');
  if (!fs.existsSync(configPath)) die(`Missing ${configPath}`);
  // Node 22's type stripping loads the project-authored TypeScript contract.
  const loaded = await import(pathToFileURL(configPath).href);
  const config = loaded.default ?? loaded.project;
  if (!config?.entryPoint || !config?.videosDir || !config?.contentDir || !config?.theme || !Array.isArray(config.styles)) die('Invalid videogen.config.ts');
  // A draft can have its own Remotion entry without bundling every archived film.
  const perVideo = videoId ? path.join(cwd, config.videosDir, safeId(videoId), "entry.tsx") : null;
  const entryPoint = videoId && config.entryPointForVideo ? config.entryPointForVideo(safeId(videoId)) :
    perVideo && fs.existsSync(perVideo) ? perVideo : config.entryPoint;
  if (typeof entryPoint !== 'string' || !entryPoint) die('Invalid video entry point');
  return {...config, entryPoint: path.resolve(cwd, entryPoint), videosDir: path.resolve(cwd, config.videosDir), contentDir: path.resolve(cwd, config.contentDir), publicDir: path.resolve(cwd, config.publicDir ?? "public"), workDir: path.resolve(cwd, config.workDir ?? "tmp"), sourceCacheDir: path.resolve(cwd, config.sourceCacheDir ?? "tmp/source-assets")};
}
function browserExecutable(config) {
  const explicit = process.env.VIDEOGEN_BROWSER_EXECUTABLE ?? config.browserExecutable;
  if (explicit) return explicit;
  if (process.platform === 'win32') {
    for (const candidate of ['C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe']) if (fs.existsSync(candidate)) return candidate;
  }
  return undefined;
}
function metadata(config, videoId) {
  const file = path.join(config.videosDir, safeId(videoId), 'content', 'video.yaml');
  if (!fs.existsSync(file)) die(`Missing ${file}`);
  const value = parse(fs.readFileSync(file, 'utf8'));
  const compositionId = value?.video?.compositionId;
  if (!compositionId || typeof compositionId !== 'string') die(`${file}: video.compositionId is required`);
  return {file, value, compositionId, dir: path.join(config.videosDir, videoId)};
}
async function compositions(config) {
  // Programmatic bundles do not read remotion.config.ts; pass the same static root.
  const serveUrl = await bundle({entryPoint: config.entryPoint, publicDir: config.publicDir, onProgress: () => undefined});
  return getCompositions(serveUrl, {logLevel: 'error', browserExecutable: browserExecutable(config)});
}
async function composition(config, compositionId) {
  const list = await compositions(config);
  const found = list.find((item) => item.id === compositionId);
  if (!found) die(`Composition ${compositionId} is absent from ${config.entryPoint}; available: ${list.map((item) => item.id).join(', ')}`);
  return found;
}
function checks(config, videoId, kind = 'video', phase = 'validate', comp = null) {
  for (const check of config.checks ?? []) {
    if (check.appliesTo && check.appliesTo !== kind && check.appliesTo !== 'all') continue;
    if ((check.phase ?? 'validate') !== phase) continue;
    if (check.whenExists && !fs.existsSync(path.resolve(cwd, check.whenExists.replace('{id}', videoId)))) continue;
    if (check.whenFormat && comp && check.whenFormat !== (comp.width < comp.height ? 'portrait' : 'landscape')) continue;
    const values = {id: videoId, width: comp?.width, height: comp?.height, fps: comp?.fps};
    const argv = (check.args ?? ['{id}']).map((arg) => arg.replace(/\{(id|width|height|fps)\}/g, (_, key) => String(values[key] ?? '')));
    run(check.command, argv, check.name);
  }
}
function builtin(name, ...argv) {
  run(process.execPath, [path.join(toolkit, 'dist', 'gates', `check-${name}.mjs`), ...argv], name);
}
function copyTree(from, to) {
  if (fs.existsSync(to)) die(`Target already exists: ${to}`);
  fs.cpSync(from, to, {recursive: true});
}
async function main() {
  if (command === 'init') {
    const target = path.resolve(cwd, id ?? '.');
    if (fs.existsSync(target) && fs.readdirSync(target).length) die(`Target must be empty: ${target}`);
    fs.mkdirSync(target, {recursive: true});
    for (const entry of fs.readdirSync(path.join(toolkit, 'templates', 'project'))) {
      copyTree(path.join(toolkit, 'templates', 'project', entry), path.join(target, entry === 'gitignore' ? '.gitignore' : entry));
    }
    const requestedTheme = flag('theme') ?? 'neutral';
    if (!['neutral', 'revise-labs'].includes(requestedTheme)) die(`Unknown starter theme ${requestedTheme}`);
    if (requestedTheme === 'revise-labs') {
      const configPath = path.join(target, 'videogen.config.ts');
      const source = fs.readFileSync(configPath, 'utf8')
        .replaceAll('neutralTheme', 'reviseLabsTheme')
        .replaceAll('coreExplainer', 'builtInStyles');
      fs.writeFileSync(configPath, source);
      fs.cpSync(path.join(toolkit, 'assets', 'fonts'), path.join(target, 'public', 'fonts'), {recursive: true});
    }
    console.log(`Scaffolded ${target}`);
    return;
  }
  if (command === 'sync-skill') {
    const target = path.join(cwd, '.agents', 'skills', 'videogen');
    fs.mkdirSync(path.dirname(target), {recursive: true});
    if (fs.existsSync(target) && !fs.existsSync(path.join(target, '.videogen-version'))) die(`${target} is not a managed copy; inspect it before replacement`);
    if (fs.existsSync(target)) fs.rmSync(target, {recursive: true, force: true});
    // Copy the exact installed skill so agent instructions match executable code.
    for (const name of ['SKILL.md', 'references']) {
      const source = path.join(toolkit, name);
      fs.cpSync(source, path.join(target, name), {recursive: true});
    }
    const version = JSON.parse(fs.readFileSync(path.join(toolkit, '..', 'package.json'), 'utf8')).version;
    fs.writeFileSync(path.join(target, '.videogen-version'), `${version}\n`);
    console.log(`Installed version-matched skill at ${target}`);
    return;
  }
  if (command === 'scaffold') {
    const config = await project();
    const result = scaffoldDraft(config, safeId(id), {title: flag('title') ?? id, durationSeconds: Number(flag('duration') ?? 5)});
    console.log(`Scaffolded ${result.folder} as ${result.compositionId}`);
    return;
  }
  if (command === 'source' || command === 'probe') {
    const config = await project();
    // A fresh project supplies cache and palette settings; the tools stay channel neutral.
    process.env.VIDEOGEN_SOURCE_CACHE_DIR = config.sourceCacheDir;
    process.env.VIDEOGEN_PROBE_THEME = JSON.stringify(config.theme.colors);
    const script = path.join(toolkit, 'scripts', 'tools', command === 'source' ? 'article-assets.mjs' : 'frame-probe.mjs');
    const result = spawnSync(process.execPath, [script, id, ...args], {cwd, stdio: 'inherit'});
    if (result.error || result.status !== 0) die(`${command} failed: ${result.error?.message ?? `exit ${result.status}`}`);
    return;
  }
  const config = await project(['check', 'render', 'publish', 'studio'].includes(command) ? id : null);
  process.env.VIDEOGEN_VIDEOS_DIR = config.videosDir;
  if (command === 'studio') {
    metadata(config, id);
    if (!fs.existsSync(config.entryPoint)) die(`Missing draft entry: ${config.entryPoint}`);
    const remotion = path.resolve(cwd, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
    // Studio is intentionally interactive; forward the URL and shutdown signal.
    const browser = browserExecutable(config);
    const child = spawn(process.execPath, [remotion, 'studio', config.entryPoint, ...(browser ? ['--browser-executable', browser] : []), ...args], {cwd, stdio: 'inherit'});
    await new Promise((resolve, reject) => {
      child.once('error', reject);
      child.once('exit', (code) => code === 0 ? resolve() : reject(new Error(`Studio exited ${code}`)));
    });
    return;
  }
  process.env.VIDEOGEN_CONTENT_DIR = config.contentDir;
  process.env.VIDEOGEN_SOURCE_CACHE_DIR = config.sourceCacheDir;
  process.env.VIDEOGEN_EVIDENCE_STYLES = JSON.stringify(config.styles.filter((style) => style.requiresFirsthandEvidence).map((style) => style.id));
  if (command === 'styles') {
    for (const style of config.styles) console.log(`${style.id}: ${style.name} (${style.formats.join(', ')})`);
    return;
  }
  if (command === 'catalog') {
    const videos = fs.readdirSync(config.videosDir, {withFileTypes: true}).filter((entry) => entry.isDirectory() && fs.existsSync(path.join(config.videosDir, entry.name, 'video.tsx'))).map((entry) => entry.name).sort();
    const sharedCompositions = config.entryPointForVideo ? null : await compositions(config);
    for (const videoId of videos) {
      const item = metadata(config, videoId);
      const localEntry = path.join(config.videosDir, videoId, 'entry.tsx');
      const videoConfig = config.entryPointForVideo || fs.existsSync(localEntry) ? await project(videoId) : config;
      const list = videoConfig === config ? sharedCompositions : await compositions(videoConfig);
      const comp = list.find((composition) => composition.id === item.compositionId);
      if (!comp) die(`${videoId}: missing composition ${item.compositionId}`);
      const declaredWidth = Number(item.value.video?.width);
      const declaredHeight = Number(item.value.video?.height);
      if (declaredWidth && declaredWidth !== comp.width || declaredHeight && declaredHeight !== comp.height) die(`${videoId}: metadata dimensions disagree with Remotion`);
      console.log(`${videoId}: ${comp.id} ${comp.width}x${comp.height} ${comp.durationInFrames} @ ${comp.fps}`);
    }
    console.log(`Verified ${videos.length} implemented videos against Remotion compositions`);
    return;
  }
  if (command === 'gate') {
    const allowed = new Set(['animation-core', 'layout-video', 'camera-clearance', 'motion', 'min-font', 'media-quality', 'evidence', 'creative-review']);
    if (!allowed.has(id)) die(`Unknown gate ${id}`);
    builtin(id, ...args);
    return;
  }
  if (command === 'narration') {
    const item = metadata(config, id);
    if (!fs.existsSync(path.join(item.dir, 'content', 'narration.yaml'))) die(`${id} has no narration.yaml`);
    run(process.execPath, [path.join(toolkit, 'scripts', 'narration.mjs'), item.dir], 'Narration');
    return;
  }
  if (command === 'publish') {
    const item = metadata(config, id);
    const confirm = hasFlag('confirm');
    if (confirm) run(process.execPath, [fileURLToPath(import.meta.url), 'check', id], 'Prepublish validation');
    const result = await publishYoutube(item, config, {confirm, resume: hasFlag('resume'), at: flag('at')});
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  if (command === 'check' || command === 'render') {
    const item = metadata(config, id);
    const narrated = fs.existsSync(path.join(item.dir, 'content', 'narration.yaml'));
    if (narrated) run(process.execPath, [path.join(toolkit, 'scripts', 'verify-narration.mjs'), item.dir], 'Narration cache');
    checks(config, id, 'video', 'prepare');
    const mainComp = await composition(config, item.compositionId);
    const isTrailer = hasFlag('trailer');
    const comp = isTrailer ? await composition(config, item.value.video?.trailerCompositionId ?? `${item.compositionId}Trailer`) : mainComp;
    const fixed = Number(item.value.video?.durationSeconds);
    if (Number.isFinite(fixed) && fixed > 0 && Math.abs(mainComp.durationInFrames / mainComp.fps - fixed) > 1 / mainComp.fps) die(`${id}: composition duration disagrees with fixed durationSeconds`);
    builtin('animation-core');
    if (item.value.video?.style && JSON.parse(process.env.VIDEOGEN_EVIDENCE_STYLES).includes(item.value.video.style)) builtin('evidence', id);
    builtin('media-quality', id);
    if (narrated || (Number.isFinite(fixed) && fixed > 0)) builtin('layout-video', id, `${mainComp.width}x${mainComp.height}`);
    if (narrated) {
      builtin('camera-clearance', id);
      builtin('min-font', id);
      if (fs.existsSync(path.join(item.dir, 'timeline.ts'))) builtin('motion', id);
    }
    if (fs.existsSync(path.join(item.dir, 'research', 'creative-review.yaml'))) builtin('creative-review', id);
    checks(config, id, 'video', 'validate', comp);
    console.log(`${id}: ${comp.id} ${comp.width}x${comp.height} ${comp.durationInFrames} frames @ ${comp.fps} fps`);
    if (command === 'check') return;
    let from = flag('from');
    let to = flag('to');
    const phase = flag('phase') ?? flag('phases');
    if (phase && isTrailer) die('Trailer selection uses seconds, not narration phases');
    if (phase && (from !== null || to !== null)) die('Use either phase selection or time selection');
    if (phase) {
      if (!narrated) die('Phase selection needs narration');
      const source = fs.readFileSync(path.join(item.dir, 'assets', 'generated', 'narration.ts'), 'utf8');
      const match = source.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
      if (!match) die('Could not read generated narration cues');
      const cues = JSON.parse(match[1]);
      const parts = phase.split(',').map((part) => part.match(/^(\d+)(?:-(\d+))?$/));
      if (parts.some((part) => !part)) die('A phase must be N, N-M, or comma-separated ranges');
      const context = Number(flag('context') ?? 0);
      if (!Number.isInteger(context) || context < 0) die('Context must be a nonnegative integer');
      const first = Math.max(1, Math.min(...parts.map((part) => Number(part[1]))) - context);
      const last = Math.min(cues.length, Math.max(...parts.map((part) => Number(part[2] ?? part[1]))) + context);
      if (first > cues.length || last < first) die('Phase is outside narration');
      from = String(cues[first - 1].startSeconds);
      to = String(cues[last - 1].endSeconds);
    }
    if ((from == null) !== (to == null)) die('Use --from and --to together');
    if (!hasFlag('delivery') && (from == null || to == null)) die('A development render needs --from and --to; full delivery requires --delivery');
    const remotion = path.resolve(cwd, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
    const outputDir = path.join(item.dir, 'assets', 'generated', 'video');
    fs.mkdirSync(outputDir, {recursive: true});
    const range = from == null ? null : {start: Number(from), end: Number(to)};
    if (range && (!Number.isFinite(range.start) || !Number.isFinite(range.end) || range.start < 0 || range.end <= range.start || range.end > comp.durationInFrames / comp.fps)) die('Invalid render range');
    const width = flag('width');
    const height = flag('height');
    const scaleFlag = flag('scale');
    if (scaleFlag && (width || height)) die('Use --scale or --width/--height');
    const scale = Number(scaleFlag ?? (config.renderShortSide ?? 1440) / Math.min(comp.width, comp.height));
    if (!Number.isFinite(scale) || scale <= 0) die('Invalid render scale');
    const effWidth = width == null ? Math.round(comp.width * scale) : Number(width);
    const effHeight = height == null ? Math.round(comp.height * scale) : Number(height);
    if (!Number.isInteger(effWidth) || !Number.isInteger(effHeight) || effWidth <= 0 || effHeight <= 0) die('Invalid render dimensions');
    const resolution = width || height ? [...(width ? ['--width', String(effWidth)] : []), ...(height ? ['--height', String(effHeight)] : [])] : ['--scale', String(scale)];
    let endFrame = comp.durationInFrames - 1;
    if (!range && narrated && !hasFlag('follow-us') && !isTrailer) {
      const source = fs.readFileSync(path.join(item.dir, 'assets', 'generated', 'narration.ts'), 'utf8');
      const match = source.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
      if (match) {
        const cues = JSON.parse(match[1]);
        endFrame = Math.min(endFrame, Math.ceil(Number(cues[cues.length - 1]?.endSeconds) * comp.fps) - 1);
      }
    }
    const frames = range ? ['--frames', `${Math.floor(range.start * comp.fps)}-${Math.min(comp.durationInFrames - 1, Math.ceil(range.end * comp.fps) - 1)}`] : endFrame < comp.durationInFrames - 1 ? ['--frames', `0-${endFrame}`] : [];
    const name = `${id}${isTrailer ? '-trailer' : ''}-${effWidth}x${effHeight}-${comp.fps}${range ? `-${range.start}-${range.end}` : ''}${hasFlag('follow-us') ? '-follow' : ''}.mp4`;
    const browser = browserExecutable(config);
    run(process.execPath, [remotion, 'render', config.entryPoint, comp.id, path.join(outputDir, name), ...resolution, ...frames,
      ...(browser ? ['--browser-executable', browser] : []), '--log=error'], 'Remotion render');
    console.log(path.join(outputDir, name));
    return;
  }
  if (command === 'content-check' || command === 'content-render') {
    safeId(id);
    process.env.VIDEOGEN_PROJECT = JSON.stringify({contentDir: config.contentDir, videosDir: config.videosDir, publishedDirs: config.publishedDirs?.map((dir) => path.resolve(cwd, dir)), styles: config.styles, theme: config.theme, entryPoint: config.entryPoint, contentEntryPoint: config.contentEntryPoint ? path.resolve(cwd, config.contentEntryPoint) : undefined, publicDir: config.publicDir, workDir: config.workDir, sourceCacheDir: config.sourceCacheDir});
    const contentFile = path.join(config.contentDir, id, 'content.yaml');
    if (fs.existsSync(contentFile) && JSON.parse(process.env.VIDEOGEN_EVIDENCE_STYLES).includes(parse(fs.readFileSync(contentFile, 'utf8'))?.style)) builtin('evidence', id);
    checks(config, id, 'content');
    run(process.execPath, [path.join(toolkit, 'scripts', command === 'content-check' ? 'content-check.mjs' : 'content-render.mjs'), id, ...args], command);
    return;
  }
  die('Usage: videogen <init|scaffold|sync-skill|source|probe|studio|narration|gate|check|render|publish|content-check|content-render> [id]');
}

main().catch((error) => {console.error(`videogen: ${error.message}`); process.exitCode = 1;});
