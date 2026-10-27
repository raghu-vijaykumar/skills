import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {parse} from 'yaml';

// This serialized project contract comes from videogen.config.ts in the CLI.

const MEDIA_KINDS = new Set(['image', 'gif', 'video']);
const KINDS = new Set(['text', ...MEDIA_KINDS]);

function resolveVideoYaml(project, videoId) {
  const draft = path.resolve(project.videosDir ?? 'videos', videoId, 'content', 'video.yaml');
  if (fs.existsSync(draft)) return draft;
  for (const dir of project.publishedDirs ?? []) {
    const base = path.resolve(dir);
    if (!fs.existsSync(base)) continue;
    for (const name of fs.readdirSync(base)) {
      const folder = path.join(base, name);
      const provenance = path.join(folder, 'source-provenance.json');
      const candidate = path.join(folder, 'content', 'video.yaml');
      if (!fs.existsSync(provenance) || !fs.existsSync(candidate)) continue;
      try {
        if (JSON.parse(fs.readFileSync(provenance, 'utf8')).sourceId === videoId) return candidate;
      } catch {
        continue;
      }
    }
  }
  return draft;
}

export function loadContentPackage(id) {
  const project = JSON.parse(process.env.VIDEOGEN_PROJECT ?? '{}');
  if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(id ?? '')) throw new Error('Content ID must be a slug');
  const root = process.cwd();
  const dir = path.resolve(project.contentDir ?? 'content', id);
  const configPath = path.join(dir, 'content.yaml');
  if (!fs.existsSync(configPath)) throw new Error(`Missing ${configPath}`);
  const config = parse(fs.readFileSync(configPath, 'utf8'));
  if (config?.id !== id) throw new Error(`${configPath}: id must be ${id}`);
  const style = (project.styles ?? []).find((item) => item.id === config.style);
  if (!style) throw new Error(`${configPath}: unknown content style ${config.style}`);
  if (!config.title?.trim()) throw new Error(`${configPath}: title is required before rendering editions`);
  const relative = config.source?.assetManifest;
  const manifestPath = relative ? path.resolve(dir, relative) : null;
  if (!manifestPath || !manifestPath.startsWith(`${root}${path.sep}`) || !fs.existsSync(manifestPath)) throw new Error(`${configPath}: source.assetManifest must resolve to an existing repository manifest`);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const cacheDir = path.resolve(manifest.cacheDir ?? path.join('tmp', 'source-assets', id));
  const cacheRoot = path.resolve('tmp', 'source-assets');
  if (!cacheDir.startsWith(`${cacheRoot}${path.sep}`)) throw new Error(`${manifestPath}: cacheDir must stay inside tmp/source-assets`);
  const assets = new Map();
  for (const asset of manifest.assets ?? []) {
    if (!/^[a-z0-9][a-z0-9-]*$/.test(asset.id ?? '') || assets.has(asset.id)) throw new Error(`${manifestPath}: asset IDs must be unique slugs`);
    assets.set(asset.id, asset);
  }
  const editions = config.editions ?? {};
  if (!editions.video && !editions.carousel && !editions.post) throw new Error(`${configPath}: add a video, carousel, or post edition`);
  if (editions.video) {
    if (!style.formats.includes('video')) throw new Error(`${style.name} does not support video`);
    const videoId = editions.video.videoId;
    if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(videoId ?? '')) throw new Error('Video edition needs a valid videoId');
    const videoYamlPath = resolveVideoYaml(project, videoId);
    if (!fs.existsSync(videoYamlPath)) throw new Error(`Video edition missing ${videoYamlPath}`);
    const videoYaml = parse(fs.readFileSync(videoYamlPath, 'utf8'));
    if (videoYaml.video?.style !== config.style) throw new Error(`Video edition ${videoId} must use style ${config.style}`);
    if (style.requiresFirsthandEvidence && videoYaml.source?.contentId !== id) throw new Error(`${style.name} video ${videoId} must reference source.contentId: ${id}`);
  }

  const probed = new Map();
  const probe = (asset) => {
    if (probed.has(asset.id)) return probed.get(asset.id);
    const file = path.join(cacheDir, asset.file);
    const result = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', file], {encoding: 'utf8'});
    if (result.error || result.status !== 0) throw new Error(`Cannot probe source media ${asset.id}: ${result.stderr?.trim() || result.error?.message}`);
    const info = JSON.parse(result.stdout);
    const details = {width: Number(info.streams?.[0]?.width), height: Number(info.streams?.[0]?.height), duration: Number(info.format?.duration)};
    if (!Number.isFinite(details.width) || !Number.isFinite(details.height) || details.width <= 0 || details.height <= 0) throw new Error(`Source media ${asset.id} has no usable dimensions`);
    probed.set(asset.id, details);
    return details;
  };
  const validateCard = (card, label, canvas) => {
    if (!card || !KINDS.has(card.kind)) throw new Error(`${label}: kind must be text, image, gif, or video`);
    if (!card.heading?.trim() && !card.body?.trim()) throw new Error(`${label}: heading or body is required`);
    if (MEDIA_KINDS.has(card.kind) && !card.evidenceId) throw new Error(`${label}: ${card.kind} requires evidenceId`);
    if (card.evidenceId) {
      const asset = assets.get(card.evidenceId);
      if (!asset || asset.used === false) throw new Error(`${label}: evidenceId ${card.evidenceId} is not a used source asset`);
      if (!asset.file || path.basename(asset.file) !== asset.file) throw new Error(`${label}: source asset file must be a single cache filename`);
      if (!fs.existsSync(path.join(cacheDir, asset.file))) throw new Error(`${label}: cached source missing for ${card.evidenceId}`);
      if (!asset.attribution?.trim()) throw new Error(`${label}: source attribution is required for ${card.evidenceId}`);
      const ext = path.extname(asset.file).toLowerCase();
      if (card.kind === 'image' && !['.png', '.jpg', '.jpeg', '.webp'].includes(ext)) throw new Error(`${label}: image needs a still raster source`);
      if (card.kind === 'gif' && !['.gif', '.mp4', '.mov', '.webm'].includes(ext)) throw new Error(`${label}: gif needs animated source media`);
      if (card.kind === 'video' && !['.mp4', '.mov', '.webm', '.gif'].includes(ext)) throw new Error(`${label}: video needs animated source media`);
      if (MEDIA_KINDS.has(card.kind)) {
        const info = probe(asset);
        const width = canvas?.width ?? 1080;
        const height = canvas?.height ?? 1350;
        const mediaWidth = width - 128 * (width / 1080);
        const mediaHeight = height * 0.44;
        const scale = Math.min(mediaWidth / info.width, mediaHeight / info.height);
        if (scale > 1.01) throw new Error(`${label}: ${asset.id} would be enlarged ${scale.toFixed(2)}x in the media window`);
        if ((card.kind === 'gif' || card.kind === 'video') && Number.isFinite(info.duration) && (card.startSeconds ?? 0) + card.durationSeconds > info.duration + 0.05) throw new Error(`${label}: requested excerpt exceeds source duration`);
      }
    }
    if (card.kind === 'gif' || card.kind === 'video') {
      if (!Number.isFinite(card.durationSeconds) || card.durationSeconds <= 0) throw new Error(`${label}: durationSeconds must be positive`);
      if (card.startSeconds !== undefined && (!Number.isFinite(card.startSeconds) || card.startSeconds < 0)) throw new Error(`${label}: startSeconds must be nonnegative`);
    }
  };
  if (editions.carousel) {
    if (!style.formats.includes('carousel')) throw new Error(`${style.name} does not support carousel`);
    if (!Array.isArray(editions.carousel.slides) || !editions.carousel.slides.length) throw new Error('Carousel needs at least one slide');
    const ids = new Set();
    for (const [index, slide] of editions.carousel.slides.entries()) {
      if (!slide.id || !/^[a-z0-9][a-z0-9-]*$/.test(slide.id) || ids.has(slide.id)) throw new Error(`Carousel slide ${index + 1} needs a unique slug id`);
      ids.add(slide.id);
      validateCard(slide, `Carousel slide ${slide.id}`, editions.carousel.canvas);
    }
  }
  if (editions.post) {
    if (!style.formats.includes('post')) throw new Error(`${style.name} does not support post`);
    if (!editions.post.caption?.trim()) throw new Error('Post caption is required');
    validateCard(editions.post, 'Post', editions.post.canvas);
  }
  return {id, dir, config, style, manifest, manifestPath, cacheDir, assets};
}
