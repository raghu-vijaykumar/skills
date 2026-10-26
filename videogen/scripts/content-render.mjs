// Render one format edition from a shared content package. Source originals
// remain in tmp/source-assets; staged copies and exported cards are ignored.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {loadContentPackage} from './content-package.mjs';
const project = JSON.parse(process.env.VIDEOGEN_PROJECT ?? '{}');

const [id, ...args] = process.argv.slice(2);
if (args.length && (args.length !== 2 || args[0] !== '--format')) {
  console.error('Usage: npm run content:render -- <content-id> [--format carousel|post|all]');
  process.exit(1);
}
const requested = args[0] === '--format' ? args[1] : 'all';
if (!['all', 'carousel', 'post'].includes(requested)) {
  console.error('Usage: npm run content:render -- <content-id> [--format carousel|post|all]');
  process.exit(1);
}

function run(command, commandArgs, label) {
  const result = spawnSync(command, commandArgs, {encoding: 'utf8', maxBuffer: 30 * 1024 * 1024});
  if (result.error || result.status !== 0) {
    const output = `${result.stdout ?? ''}\n${result.stderr ?? ''}`.trim().split(/\r?\n/).filter(Boolean);
    throw new Error(`${label} failed: ${result.error?.message ?? output.slice(-8).join('\n')}`);
  }
}

try {
  const loaded = loadContentPackage(id);
  run(process.execPath, [fileURLToPath(new URL('./content-check.mjs', import.meta.url)), id], 'Content validation');
  const formats = requested === 'all' ? ['carousel', 'post'].filter((format) => loaded.config.editions[format]) : [requested];
  if (formats.some((format) => !loaded.config.editions[format])) throw new Error(`${requested} edition is not defined`);
  const stageDir = path.resolve('public', 'content-assets', id);
  const propsDir = path.resolve('tmp', 'content-render', id);
  const outputRoot = path.resolve('out', 'content', id);
  fs.mkdirSync(stageDir, {recursive: true});
  fs.mkdirSync(propsDir, {recursive: true});
  fs.mkdirSync(outputRoot, {recursive: true});
  const cli = path.resolve('node_modules', '@remotion', 'cli', 'remotion-cli.js');
  const entry = project.contentEntryPoint ?? fileURLToPath(new URL('../runtime/content/entry.tsx', import.meta.url));
  const exported = [];

  const stage = (asset, kind) => {
    if (!asset) return null;
    const source = path.join(loaded.cacheDir, asset.file);
    const ext = path.extname(asset.file).toLowerCase();
    const target = path.join(stageDir, asset.file);
    fs.copyFileSync(source, target);
    if (ext === '.gif' && (kind === 'gif' || kind === 'video')) {
      const transcoded = path.join(stageDir, `${asset.id}-gif-source.mp4`);
      run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', target, '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', transcoded], 'GIF staging');
      return `content-assets/${id}/${path.basename(transcoded)}`;
    }
    return `content-assets/${id}/${asset.file}`;
  };

  const renderCard = (card, format, basename) => {
    const asset = card.evidenceId ? loaded.assets.get(card.evidenceId) : null;
    const mediaAsset = stage(asset, card.kind);
    const width = loaded.config.editions[format].canvas?.width ?? 1080;
    const height = loaded.config.editions[format].canvas?.height ?? 1350;
    const props = {
      style: loaded.style.id,
      styleName: loaded.style.name,
      theme: project.theme,
      kind: card.kind,
      phase: card.phase,
      heading: card.heading ?? loaded.config.title,
      body: card.body,
      claimKind: card.claimKind,
      mediaAsset,
      evidence: asset ? {id: asset.id, attribution: asset.attribution, capturedAt: asset.evidence?.capturedAt, method: asset.evidence?.method} : undefined,
      startSeconds: card.startSeconds ?? 0,
      durationSeconds: card.durationSeconds ?? 1,
      width,
      height,
    };
    const formatDir = path.join(outputRoot, format);
    fs.mkdirSync(formatDir, {recursive: true});
    const propsPath = path.join(propsDir, `${format}-${basename}.json`);
    fs.writeFileSync(propsPath, JSON.stringify(props));
    const extension = card.kind === 'video' ? '.mp4' : card.kind === 'gif' ? '.gif' : '.png';
    const output = path.join(formatDir, `${basename}${extension}`);
    if (card.kind === 'video' || card.kind === 'gif') {
      const mp4 = card.kind === 'gif' ? path.join(propsDir, `${format}-${basename}.mp4`) : output;
      run(process.execPath, [cli, 'render', entry, 'ContentCard', mp4, `--props=${propsPath}`, '--codec=h264', '--crf=18'], `Render ${format}/${basename}`);
      if (card.kind === 'gif') {
        const filter = '[0:v]fps=15,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3';
        run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', mp4, '-filter_complex', filter, '-loop', '0', output], `GIF ${format}/${basename}`);
      }
    } else {
      run(process.execPath, [cli, 'still', entry, 'ContentCard', output, `--props=${propsPath}`, '--frame=0'], `Render ${format}/${basename}`);
    }
    return {file: path.relative(outputRoot, output).replace(/\\/g, '/'), kind: card.kind, evidenceId: card.evidenceId ?? null, sourceUrl: asset?.sourceUrl ?? null, attribution: asset?.attribution ?? null};
  };

  if (formats.includes('carousel')) {
    const edition = loaded.config.editions.carousel;
    for (const [index, slide] of edition.slides.entries()) exported.push(renderCard(slide, 'carousel', `slide-${String(index + 1).padStart(2, '0')}-${slide.id}`));
    fs.writeFileSync(path.join(outputRoot, 'carousel', 'caption.md'), `${edition.caption ?? loaded.config.title}\n`);
  }
  if (formats.includes('post')) {
    exported.push(renderCard(loaded.config.editions.post, 'post', 'post'));
    fs.writeFileSync(path.join(outputRoot, 'post', 'caption.md'), `${loaded.config.editions.post.caption}\n`);
  }
  const outputManifest = path.join(outputRoot, 'manifest.json');
  const previous = fs.existsSync(outputManifest) ? JSON.parse(fs.readFileSync(outputManifest, 'utf8')) : {files: []};
  const retained = (previous.files ?? []).filter((file) => !formats.some((format) => file.file.startsWith(`${format}/`)));
  const current = new Set(exported.map((file) => file.file));
  for (const old of previous.files ?? []) {
    if (!formats.some((format) => old.file.startsWith(`${format}/`)) || current.has(old.file)) continue;
    const stalePath = path.resolve(outputRoot, old.file);
    if (!stalePath.startsWith(`${outputRoot}${path.sep}`)) throw new Error(`Unsafe stale output path: ${old.file}`);
    if (fs.existsSync(stalePath)) fs.unlinkSync(stalePath);
  }
  fs.writeFileSync(outputManifest, `${JSON.stringify({contentId: id, style: loaded.style.id, files: [...retained, ...exported]}, null, 2)}\n`);
  console.log(`Content render: ${id} exported ${exported.length} asset(s) to ${outputRoot}`);
} catch (error) {
  console.error(`Content render: ${error.message}`);
  process.exit(1);
}
