// File-backed LinkedIn approvals survive chat boundaries and expire when inputs change.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {validatePreflight} from './preflight.mjs';
import {validateSrt} from './package.mjs';
import {connectLinkedin, publishLinkedin} from './linkedin-publish.mjs';

const bundle = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const preflight = path.join(bundle, 'skills', 'content-studio-workflow', 'scripts', 'preflight.py');
const stages = ['angle', 'draft', 'final'];
const requiredBrief = ['angle', 'stance', 'audience', 'formatReason'];

export function defaultWorkspace() {
  return process.env.CONTENT_STUDIO_LINKEDIN_WORKSPACE ??
    (process.platform === 'win32' ? 'C:\\workspace\\content\\linkedin-personal' : path.join(os.homedir(), 'content', 'linkedin-personal'));
}

export function option(args, name) {
  const index = args.indexOf(`--${name}`);
  if (index < 0) return null;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error(`--${name} needs a value`);
  return value;
}
const flag = (args, name) => args.includes(`--${name}`);
const read = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
const write = (file, value) => {
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const temp = `${file}.tmp`;
  fs.writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`);
  fs.renameSync(temp, file);
};
const hash = (values) => createHash('sha256').update(values.map((value) => String(value)).join('\0')).digest('hex');
const fileHash = (file) => {
  if (!fs.existsSync(file)) return null;
  const digest = createHash('sha256');
  const handle = fs.openSync(file, 'r');
  const block = Buffer.alloc(1024 * 1024);
  try { let size; while ((size = fs.readSync(handle, block, 0, block.length, null)) > 0) digest.update(block.subarray(0, size)); }
  finally { fs.closeSync(handle); }
  return digest.digest('hex');
};

function ensureIgnore(workspace) {
  fs.mkdirSync(workspace, {recursive: true});
  const ignore = path.join(workspace, '.gitignore');
  const current = fs.existsSync(ignore) ? fs.readFileSync(ignore, 'utf8') : '';
  const additions = ['secrets/', 'drafts/**/image.png', 'drafts/**/animation.gif', 'drafts/**/carousel.pdf',
    'drafts/**/video.mp4', 'drafts/**/cover.png',
    'drafts/**/captions.srt', 'drafts/**/.content-studio/render-public/', 'drafts/**/.content-studio/tmp/',
    'drafts/**/.content-studio/preflight/system.json'];
  const missing = additions.filter((line) => !current.split(/\r?\n/).includes(line));
  if (missing.length) fs.appendFileSync(ignore, `${current && !current.endsWith('\n') ? '\n' : ''}${missing.join('\n')}\n`);
}

function runPreflight(draft, ...args) {
  const result = spawnSync(process.env.PYTHON ?? 'python', [preflight, '--folder', draft, ...args], {encoding: 'utf8'});
  if (result.error || result.status !== 0) throw new Error(`LinkedIn precheck: ${result.error?.message ?? (result.stderr || result.stdout).trim().split(/\r?\n/).slice(-4).join(' ')}`);
  return result.stdout.trim();
}

export function draftPath(workspace, id) {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(id ?? '')) throw new Error('LinkedIn draft ID must be a lowercase slug');
  return path.join(path.resolve(workspace), 'drafts', id);
}

function presetFile(draft, brand) {
  return path.join(path.dirname(path.dirname(draft)), 'presets', `${brand}.json`);
}

function presetFor(draft, brand) {
  const file = presetFile(draft, brand);
  if (fs.existsSync(file)) {
    const preset = read(file);
    if (!String(preset.name ?? '').trim()) throw new Error(`Preset ${brand} needs a name`);
    return preset;
  }
  if (['personal', 'revise-labs'].includes(brand)) return null;
  throw new Error(`Create a reusable project preset at ${file}`);
}

function selectedFiles(draft, brief) {
  if (brief.format === 'image') return ['image.png'];
  if (brief.format === 'animated-image') return ['animation.gif'];
  if (brief.format === 'carousel') return ['carousel.pdf'];
  if (brief.format === 'video') return ['video.mp4', 'cover.png', ...(brief.narration === 'narrated' ? ['captions.srt'] : [])];
  return [];
}

function validateSources(sources) {
  if (!Array.isArray(sources.claims) || !Array.isArray(sources.assets)) throw new Error('sources.json needs claims and assets arrays');
  for (const claim of sources.claims) {
    if (!String(claim.text ?? '').trim() || !['fact', 'opinion'].includes(claim.type)) throw new Error('Each claim needs text and type fact or opinion');
    if (claim.type === 'fact' && !/^https?:\/\//.test(claim.sourceUrl ?? '')) throw new Error(`Factual claim needs a source URL: ${claim.text}`);
  }
  for (const asset of sources.assets) {
    if (!String(asset.id ?? '').trim() || !String(asset.origin ?? '').trim() || !String(asset.rights ?? '').trim()) throw new Error('Each source asset needs id, origin and rights');
  }
}

function validateBrief(brief) {
  for (const key of requiredBrief) if (!String(brief[key] ?? '').trim()) throw new Error(`brief.json needs ${key}`);
  if (!['text', 'image', 'animated-image', 'carousel', 'video'].includes(brief.format))
    throw new Error('brief.json format must be text, image, animated-image, carousel or video');
  if (!/^[a-z0-9][a-z0-9-]*$/.test(brief.brand ?? '')) throw new Error('brief.json brand needs a preset slug');
  if (brief.format === 'video' && !['narrated', 'silent'].includes(brief.narration)) throw new Error('Video needs narrated or silent choice');
  if (!String(brief.language ?? '').trim()) throw new Error('brief.json needs language');
}

function validateProductionPlan(draft, format) {
  const plan = read(path.join(draft, '.content-studio', 'preflight', 'plan.json'));
  const production = plan.steps?.find((step) => step.id === 'S04');
  if (!production?.method_id || !String(production.fallback ?? '').trim() || !Array.isArray(production.inputs) || !production.inputs.length)
    throw new Error('LinkedIn plan S04 needs method_id, inputs and fallback before angle approval');
  if (format !== 'text' && (!Array.isArray(production.command) || !production.command.length ||
      !production.command.every((part) => typeof part === 'string' && part.length)))
    throw new Error('Media plan S04 needs the exact production command argv');
}

function validateDraft(draft, brief) {
  const post = fs.readFileSync(path.join(draft, 'post.md'), 'utf8').trim();
  if (!post) throw new Error('post.md needs reviewed LinkedIn copy');
  const creative = read(path.join(draft, 'creative.json'));
  if (['image', 'animated-image'].includes(brief.format)) {
    if (!String(creative.imageConcept ?? '').trim() || !String(creative.altText ?? '').trim()) throw new Error('Image needs concept and alt text');
    if (!['original-illustration', 'evidence'].includes(creative.mediaOrigin)) throw new Error('Image needs original-illustration or evidence origin');
    if (creative.mediaOrigin === 'evidence' && !creative.evidenceId) throw new Error('Evidence image needs evidenceId');
    if (creative.mediaOrigin === 'original-illustration' && !String(creative.assetMethod ?? '').trim()) throw new Error('Original illustration needs assetMethod provenance');
  }
  if (brief.format === 'animated-image' && !String(creative.motionPlan ?? '').trim())
    throw new Error('Animated image needs a motionPlan');
  if (brief.format === 'carousel' && (!String(creative.title ?? '').trim() ||
      !Array.isArray(creative.slideOutline) || creative.slideOutline.length < 2 ||
      creative.slideOutline.some((slide) => !String(slide ?? '').trim())))
    throw new Error('Carousel needs a title and at least two outlined slides');
  if (brief.format === 'video') {
    if (!String(creative.script ?? '').trim() || !Array.isArray(creative.storyboard) || !creative.storyboard.length) throw new Error('Video needs script and storyboard');
    if (!String(creative.coverConcept ?? '').trim()) throw new Error('Video needs coverConcept');
  }
  return {post, creative};
}

function probe(file, countFrames = false) {
  const result = spawnSync('ffprobe', ['-v', 'error', ...(countFrames ? ['-count_frames'] : []), '-show_entries',
    'format=duration:stream=codec_type,codec_name,width,height,nb_read_frames', '-of', 'json', file], {encoding: 'utf8'});
  if (result.error || result.status !== 0) throw new Error(`Cannot inspect ${path.basename(file)}: ${result.error?.message ?? result.stderr.trim()}`);
  const info = JSON.parse(result.stdout);
  const video = info.streams?.find((stream) => stream.codec_type === 'video');
  if (video?.width !== 1080 || video?.height !== 1350) throw new Error(`${path.basename(file)} must be 1080x1350`);
  return {duration: Number(info.format?.duration ?? 0), frames: Number(video.nb_read_frames ?? 0), videoCodec: video.codec_name,
    audioCodec: info.streams?.find((stream) => stream.codec_type === 'audio')?.codec_name ?? null};
}

function validateFinal(draft, brief, creative) {
  if (brief.format === 'text') return {};
  const media = Object.fromEntries(selectedFiles(draft, brief).map((name) => {
    const file = path.join(draft, name);
    if (!fs.existsSync(file)) throw new Error(`Missing final asset ${name}`);
    return [name, file];
  }));
  if (['image', 'animated-image'].includes(brief.format)) {
    const details = probe(media[brief.format === 'image' ? 'image.png' : 'animation.gif'], brief.format === 'animated-image');
    if (details.videoCodec !== (brief.format === 'image' ? 'png' : 'gif')) throw new Error('LinkedIn image format does not match the approved edition');
    if (brief.format === 'animated-image' && (details.frames < 2 || details.frames > 250))
      throw new Error('LinkedIn animated GIF needs 2–250 frames');
    if (creative.mediaOrigin === 'evidence') {
      const sources = read(path.join(draft, 'sources.json'));
      if (!sources.assets.some((asset) => asset.id === creative.evidenceId)) throw new Error('Image evidenceId is absent from sources.json');
    }
  } else if (brief.format === 'carousel') {
    // A multi-page document is the organic member-profile swipe format.
    const result = spawnSync('pdfinfo', [media['carousel.pdf']], {encoding: 'utf8'});
    if (result.error || result.status !== 0) throw new Error(`Cannot inspect carousel.pdf: ${result.error?.message ?? result.stderr.trim()}`);
    const pages = Number(result.stdout.match(/^Pages:\s+(\d+)/m)?.[1] ?? 0);
    if (pages < 2 || pages !== creative.slideOutline.length) throw new Error('Carousel PDF pages must match its reviewed slide outline');
    const details = spawnSync('pdfinfo', ['-f', '1', '-l', String(pages), media['carousel.pdf']], {encoding: 'utf8'});
    if (details.error || details.status !== 0) throw new Error('Cannot inspect individual carousel pages');
    const sizes = [...details.stdout.matchAll(/^Page\s+\d+ size:\s+([\d.]+) x ([\d.]+) pts/gm)];
    if (sizes.length !== pages || sizes.some((size) => Math.abs(Number(size[1]) / Number(size[2]) - 1080 / 1350) > 0.01))
      throw new Error('Every carousel page must use a 4:5 portrait aspect ratio');
  } else {
    const details = probe(media['video.mp4']);
    if (probe(media['cover.png']).videoCodec !== 'png') throw new Error('Video cover must be PNG');
    if (details.duration < 45 || details.duration > 90) throw new Error('LinkedIn video must last 45–90 seconds');
    if (details.videoCodec !== 'h264') throw new Error('LinkedIn video must use H.264');
    if (brief.narration === 'narrated' && details.audioCodec !== 'aac') throw new Error('Narrated video needs AAC audio');
    if (brief.narration === 'narrated') validateSrt(media['captions.srt'], details.duration);
  }
  return media;
}

function fingerprint(draft, stage) {
  const brief = read(path.join(draft, 'brief.json'));
  const state = read(path.join(draft, 'linkedin-state.json'));
  validateBrief(brief);
  presetFor(draft, brief.brand);
  validateSources(read(path.join(draft, 'sources.json')));
  const plan = path.join(draft, '.content-studio', 'preflight', 'plan.json');
  if (stage === 'angle') return hash(['angle', fileHash(path.join(draft, 'idea.md')), fileHash(path.join(draft, 'brief.json')),
    fileHash(path.join(draft, 'sources.json')), fileHash(plan), fileHash(presetFile(draft, brief.brand))]);
  const angle = state.approvals.angle;
  if (!angle || angle.fingerprint !== fingerprint(draft, 'angle')) throw new Error('Angle approval is missing or stale');
  const {creative} = validateDraft(draft, brief);
  if (stage === 'draft') return hash(['draft', angle.fingerprint, fileHash(path.join(draft, 'post.md')), fileHash(path.join(draft, 'creative.json'))]);
  const draftApproval = state.approvals.draft;
  if (!draftApproval || draftApproval.fingerprint !== fingerprint(draft, 'draft')) throw new Error('Draft approval is missing or stale');
  const media = validateFinal(draft, brief, creative);
  return hash(['final', draftApproval.fingerprint, ...Object.values(media).map(fileHash)]);
}

export function approvedStage(draft) {
  const state = read(path.join(draft, 'linkedin-state.json'));
  let last = null;
  for (const stage of stages) {
    try {
      const expected = fingerprint(draft, stage);
      if (state.approvals[stage]?.fingerprint !== expected) break;
      last = stage;
    } catch { break; }
  }
  return last;
}

export function status(workspace, id) {
  const draft = draftPath(workspace, id);
  if (!fs.existsSync(draft)) throw new Error(`LinkedIn draft not found: ${id}`);
  const state = read(path.join(draft, 'linkedin-state.json'));
  const approved = approvedStage(draft);
  const receiptFile = path.join(draft, 'linkedin-receipt.json');
  const receipt = fs.existsSync(receiptFile) ? read(receiptFile) : null;
  return {id, draft, approved, nextReview: receipt?.postId ? null : receipt?.postAttemptedAt ? 'reconcile' :
    approved === 'final' ? 'publish' : stages[stages.indexOf(approved) + 1],
    published: Boolean(receipt?.postId), postId: receipt?.postId ?? null,
    files: {idea: path.join(draft, 'idea.md'), brief: path.join(draft, 'brief.json'), sources: path.join(draft, 'sources.json'),
      post: path.join(draft, 'post.md'), creative: path.join(draft, 'creative.json'), plan: path.join(draft, '.content-studio', 'preflight', 'plan.json')},
    createdAt: state.createdAt};
}

export function createDraft(workspace, id, idea) {
  const draft = draftPath(workspace, id);
  if (fs.existsSync(draft)) throw new Error(`LinkedIn draft already exists: ${id}`);
  if (!idea.trim()) throw new Error('An idea is required');
  ensureIgnore(workspace);
  fs.mkdirSync(draft, {recursive: true});
  fs.writeFileSync(path.join(draft, 'idea.md'), `${idea.trim()}\n`);
  write(path.join(draft, 'brief.json'), {angle: '', stance: '', audience: '', format: '', formatReason: '',
    brand: 'personal', narration: null, language: 'English'});
  write(path.join(draft, 'sources.json'), {claims: [], assets: []});
  fs.writeFileSync(path.join(draft, 'post.md'), '');
  write(path.join(draft, 'creative.json'), {});
  write(path.join(draft, 'linkedin-state.json'), {schemaVersion: 1, createdAt: new Date().toISOString(), approvals: {}});
  runPreflight(draft, 'profile', '--social');
  runPreflight(draft, 'init', '--kind', 'linkedin', '--goal', 'Prepare a reviewed personal LinkedIn opinion post',
    '--input', 'idea.md, brief.json and sources.json', '--deliverable', 'Approved LinkedIn copy and optional media');
  return status(workspace, id);
}

export function approve(workspace, id, stage, note) {
  if (!stages.includes(stage)) throw new Error('Approval stage must be angle, draft or final');
  if (!String(note ?? '').trim()) throw new Error('Approval needs the user review note');
  const draft = draftPath(workspace, id);
  if (stage === 'angle') {
    const brief = read(path.join(draft, 'brief.json'));
    validateBrief(brief);
    presetFor(draft, brief.brand);
    validateSources(read(path.join(draft, 'sources.json')));
    validateProductionPlan(draft, brief.format);
    runPreflight(draft, 'approve', '--note', note);
    runPreflight(draft, 'set', '--id', 'S01', '--status', 'done', '--evidence', 'idea.md and sources.json reviewed');
    runPreflight(draft, 'set', '--id', 'S02', '--status', 'done', '--evidence', note);
  }
  const digest = fingerprint(draft, stage);
  const stateFile = path.join(draft, 'linkedin-state.json');
  const state = read(stateFile);
  state.approvals[stage] = {fingerprint: digest, note: note.trim(), at: new Date().toISOString()};
  for (const later of stages.slice(stages.indexOf(stage) + 1)) delete state.approvals[later];
  write(stateFile, state);
  if (stage === 'draft') runPreflight(draft, 'set', '--id', 'S03', '--status', 'done', '--evidence', note);
  if (stage === 'final') {
    runPreflight(draft, 'set', '--id', 'S04', '--status', 'done', '--evidence', 'Exact format and media validated');
    runPreflight(draft, 'set', '--id', 'S05', '--status', 'done', '--evidence', note);
    runPreflight(draft, 'verify', '--phase', 'complete');
  }
  return status(workspace, id);
}

export async function renderImage(workspace, id) {
  const draft = draftPath(workspace, id);
  if (!['draft', 'final'].includes(approvedStage(draft))) throw new Error('Approve the draft before rendering its image');
  const brief = read(path.join(draft, 'brief.json'));
  if (brief.format !== 'image') throw new Error('render-image needs an image edition');
  const creative = read(path.join(draft, 'creative.json'));
  const card = creative.card ?? {};
  if (!String(card.heading ?? '').trim()) throw new Error('creative.json card.heading is required for the image renderer');
  const publicDir = path.join(draft, '.content-studio', 'render-public');
  fs.mkdirSync(publicDir, {recursive: true});
  let mediaAsset;
  let evidence;
  if (creative.illustrationPath || creative.mediaOrigin === 'evidence') {
    const asset = creative.mediaOrigin === 'evidence'
      ? read(path.join(draft, 'sources.json')).assets.find((item) => item.id === creative.evidenceId)
      : null;
    const source = path.resolve(draft, asset?.path ?? creative.illustrationPath ?? '');
    if (!fs.existsSync(source) || !['.png', '.jpg', '.jpeg', '.webp'].includes(path.extname(source).toLowerCase())) throw new Error('Image source is missing or unsupported');
    const staged = `linkedin-source${path.extname(source).toLowerCase()}`;
    fs.copyFileSync(source, path.join(publicDir, staged));
    mediaAsset = staged;
    evidence = asset ? {id: asset.id, attribution: asset.origin, method: asset.rights} : {method: creative.assetMethod};
  }
  const {neutralTheme, reviseLabsTheme} = await import('./../skills/content-studio-video/animation/videogen/dist/themes.js');
  const preset = presetFor(draft, brief.brand);
  const props = {style: brief.brand === 'revise-labs' ? 'tech-dispatch' : 'core-explainer',
    styleName: creative.styleName ?? preset?.name ?? (brief.brand === 'revise-labs' ? 'Tech Dispatch' : brief.brand),
    theme: creative.theme ?? preset?.theme ?? (brief.brand === 'revise-labs' ? reviseLabsTheme : neutralTheme),
    kind: mediaAsset ? 'image' : 'text', mediaAsset, mediaOrigin: creative.mediaOrigin,
    heading: card.heading, body: card.body ?? '', phase: card.phase ?? 'MY TAKE',
    evidence, width: 1080, height: 1350};
  const propsFile = path.join(draft, '.content-studio', 'image-props.json');
  write(propsFile, props);
  const output = path.join(draft, 'image.png');
  const renderTemp = path.join(draft, '.content-studio', 'tmp');
  fs.mkdirSync(renderTemp, {recursive: true});
  const cli = path.resolve(bundle, '..', 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  const entry = path.join(bundle, 'skills', 'content-studio-video', 'animation', 'videogen', 'dist', 'content', 'entry.js');
  const browser = process.env.CONTENT_STUDIO_BROWSER_EXECUTABLE ??
    (process.platform === 'win32' ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' : null);
  const result = spawnSync(process.execPath, [cli, 'still', entry, 'ContentCard', output,
    `--props=${propsFile}`, '--frame=0', `--public-dir=${publicDir}`,
    ...(browser && fs.existsSync(browser) ? [`--browser-executable=${browser}`] : [])], {cwd: path.resolve(bundle, '..'), encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
    env: {...process.env, TEMP: renderTemp, TMP: renderTemp, TMPDIR: renderTemp}});
  if (result.error || result.status !== 0) throw new Error(`Image render failed: ${result.error?.message ?? `${result.stdout}\n${result.stderr}`.trim().split(/\r?\n/).filter((line) => !/\bprogress\b|\d+%/.test(line)).slice(-22).join(' ')}`);
  probe(output);
  return {file: output, format: 'image', width: 1080, height: 1350};
}

export function buildCarousel(workspace, id) {
  const draft = draftPath(workspace, id);
  if (!['draft', 'final'].includes(approvedStage(draft))) throw new Error('Approve the draft before assembling a carousel');
  if (read(path.join(draft, 'brief.json')).format !== 'carousel') throw new Error('build-carousel needs a carousel edition');
  const slides = path.join(draft, 'slides');
  const names = fs.existsSync(slides) ? fs.readdirSync(slides).filter((name) => name.endsWith('.png')).sort() : [];
  const count = read(path.join(draft, 'creative.json')).slideOutline.length;
  if (names.length !== count) throw new Error('Carousel slide PNGs must match the approved outline');
  const output = path.join(draft, 'carousel.pdf');
  const result = spawnSync(process.env.PYTHON ?? 'python', [path.join(bundle, 'scripts', 'linkedin-carousel.py'),
    '--slides', slides, '--output', output], {encoding: 'utf8'});
  if (result.error || result.status !== 0) throw new Error(`Carousel assembly failed: ${result.error?.message ?? result.stderr.trim()}`);
  validateFinal(draft, {format: 'carousel'}, read(path.join(draft, 'creative.json')));
  return {file: output, format: 'carousel', pages: count};
}

export async function runLinkedinCommand(args) {
  const [command] = args;
  const workspace = path.resolve(option(args, 'workspace') ?? defaultWorkspace());
  if (command === 'connect') { ensureIgnore(workspace); return connectLinkedin(workspace, {clientFile: option(args, 'client-file'), port: option(args, 'port')}); }
  if (command === 'list') {
    const root = path.join(workspace, 'drafts');
    return fs.existsSync(root) ? fs.readdirSync(root, {withFileTypes: true}).filter((item) => item.isDirectory())
      .map((item) => { try { return status(workspace, item.name); } catch { return null; } }).filter(Boolean)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt)) : [];
  }
  const id = option(args, 'draft');
  if (command === 'new') {
    const ideaFile = option(args, 'idea-file');
    const idea = ideaFile ? fs.readFileSync(path.resolve(ideaFile), 'utf8') : option(args, 'idea');
    if (!idea) throw new Error('linkedin new needs --idea or --idea-file');
    const chosenId = id ?? `${new Date().toISOString().slice(0, 10)}-${idea.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40)}`;
    return createDraft(workspace, chosenId, idea);
  }
  if (!id) throw new Error(`linkedin ${command ?? 'command'} needs --draft`);
  if (command === 'status' || command === 'resume') return status(workspace, id);
  if (command === 'approve') return approve(workspace, id, option(args, 'stage'), option(args, 'note'));
  if (command === 'render-image') return renderImage(workspace, id);
  if (command === 'build-carousel') return buildCarousel(workspace, id);
  if (command === 'publish') {
    const draft = draftPath(workspace, id);
    if (approvedStage(draft) !== 'final') throw new Error('Exact final package approval is missing or stale');
    validatePreflight(draft, 'complete');
    return publishLinkedin(draft, workspace, {confirm: flag(args, 'confirm'), authorizationNote: option(args, 'authorization-note')});
  }
  throw new Error(`Unknown LinkedIn command: ${command ?? '(none)'}`);
}
