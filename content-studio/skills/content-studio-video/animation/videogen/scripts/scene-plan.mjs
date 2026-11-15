// Validate authored scene coverage and asset provenance before bundling Remotion.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export const SCENE_TYPES = new Set(['hero', 'device', 'flow', 'stack', 'code', 'data', 'document', 'presenter']);
const ORIGINS = new Set(['procedural', 'generated', 'recorded', 'licensed']);
const safeId = (value) => typeof value === 'string' && /^[a-z][a-z0-9-]*$/.test(value);
// Reject directories reserved for study footage while allowing a new video's
// legitimate assets to mention a platform or source as part of its topic.
const referencePath = (value) => /(^|[\\/])(reference|source-reel|source-media)([\\/]|$)/i.test(value);

export function validateScenePlan(folder, expected = {}) {
  const sceneFile = path.join(folder, 'scene-plan.json');
  if (!fs.existsSync(sceneFile)) return null;
  const manifestFile = path.join(folder, 'asset-manifest.json');
  if (!fs.existsSync(manifestFile)) throw new Error(`${folder}: scene-plan.json needs asset-manifest.json`);
  const plan = JSON.parse(fs.readFileSync(sceneFile, 'utf8'));
  const manifest = JSON.parse(fs.readFileSync(manifestFile, 'utf8'));
  if (plan.schemaVersion !== 1 || manifest.schemaVersion !== 1) throw new Error('Unsupported scene or asset manifest schema');
  if (plan.fps !== 30 || !Number.isInteger(plan.durationFrames) || plan.durationFrames < 1)
    throw new Error('Scene plan requires 30 fps and positive durationFrames');
  for (const dimension of ['width', 'height']) {
    if (!Number.isInteger(plan[dimension]) || plan[dimension] < 1) throw new Error(`Invalid ${dimension}`);
    if (expected[dimension] && plan[dimension] !== expected[dimension]) throw new Error(`Scene plan ${dimension} differs from composition`);
  }
  if (expected.durationInFrames && plan.durationFrames !== expected.durationInFrames)
    throw new Error('Scene plan duration differs from composition');
  if (!Array.isArray(plan.scenes) || !plan.scenes.length || !Array.isArray(manifest.assets))
    throw new Error('Scene plan needs scenes and asset manifest needs assets');
  const assets = new Map();
  for (const asset of manifest.assets) {
    if (!safeId(asset.id) || assets.has(asset.id) || !ORIGINS.has(asset.origin)) throw new Error(`Invalid asset entry: ${asset.id}`);
    if (typeof asset.path !== 'string' || !asset.path || path.isAbsolute(asset.path) ||
        asset.path.split(/[\\/]/).includes('..') || referencePath(asset.path))
      throw new Error(`Unsafe or reference asset path: ${asset.path}`);
    if (typeof asset.license !== 'string' || !asset.license.trim()) throw new Error(`Missing license for ${asset.id}`);
    const file = path.resolve(folder, asset.path);
    if (!file.startsWith(path.resolve(folder) + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile() ||
        !fs.realpathSync(file).startsWith(fs.realpathSync(folder) + path.sep))
      throw new Error(`Missing asset ${asset.id}: ${file}`);
    const hash = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    if (asset.sha256 !== hash) throw new Error(`Asset hash mismatch: ${asset.id}`);
    assets.set(asset.id, asset);
  }
  const sourceFile = path.join(folder, 'video.tsx');
  if (fs.existsSync(sourceFile)) {
    const source = fs.readFileSync(sourceFile, 'utf8');
    const imported = [...source.matchAll(/\bfrom\s+['"]([^'"]+)['"]/g)].map((match) => match[1]);
    const assetPaths = new Set(manifest.assets.map((asset) => asset.path.replaceAll('\\', '/')));
    for (const specifier of imported) {
      if (referencePath(specifier)) throw new Error(`Reference import in composition: ${specifier}`);
      if (/\.(mp3|wav|mp4|webm|png|jpe?g|svg)$/i.test(specifier)) {
        const relative = path.relative(folder, path.resolve(folder, specifier)).replaceAll('\\', '/');
        if (!assetPaths.has(relative)) throw new Error(`Unlisted media import: ${specifier}`);
      }
    }
  }
  let next = 0;
  const ids = new Set();
  for (const scene of plan.scenes) {
    if (!safeId(scene.id) || ids.has(scene.id)) throw new Error(`Invalid scene ID: ${scene.id}`);
    ids.add(scene.id);
    if (!SCENE_TYPES.has(scene.type)) throw new Error(`Unsupported scene type: ${scene.type}`);
    if (scene.startFrame !== next || !Number.isInteger(scene.endFrame) || scene.endFrame <= next)
      throw new Error(`Scene gap, overlap, or invalid frame range at ${scene.id}`);
    next = scene.endFrame;
    if (!scene.title || typeof scene.title !== 'string' || !scene.visual || typeof scene.visual !== 'object')
      throw new Error(`Missing teaching content in ${scene.id}`);
    if (!Array.isArray(scene.stateChanges) || !scene.stateChanges.length || !Array.isArray(scene.camera) || !scene.camera.length)
      throw new Error(`Scene ${scene.id} needs semantic state changes and camera keyframes`);
    // The runtime reads state changes in order and interpolates camera keys;
    // enforce that order here so an authored scene cannot silently jump back.
    let previous = scene.startFrame - 1;
    for (const state of scene.stateChanges) {
      if (!Number.isInteger(state.frame) || state.frame <= previous || state.frame >= scene.endFrame || !state.label)
        throw new Error(`Invalid state change in ${scene.id}`);
      previous = state.frame;
    }
    if (scene.stateChanges[0].frame !== scene.startFrame) throw new Error(`First state change must start ${scene.id}`);
    previous = scene.startFrame - 1;
    for (const camera of scene.camera) {
      if (!Number.isInteger(camera.frame) || camera.frame <= previous || camera.frame >= scene.endFrame ||
          !Number.isFinite(camera.scale) || camera.scale <= 0)
        throw new Error(`Invalid camera keyframe in ${scene.id}`);
      previous = camera.frame;
    }
    if (scene.camera[0].frame !== scene.startFrame) throw new Error(`First camera keyframe must start ${scene.id}`);
    if (scene.presenter?.pose && !['speaking', 'pointing', 'thinking', 'none'].includes(scene.presenter.pose))
      throw new Error(`Unsupported presenter pose in ${scene.id}`);
    for (const key of ['assetIds', 'narrationCueIds', 'sourceIds', 'audioCueIds']) {
      if (!Array.isArray(scene[key])) throw new Error(`${scene.id} needs ${key}`);
    }
    for (const id of scene.assetIds) if (!assets.has(id)) throw new Error(`Unlisted asset ${id} in ${scene.id}`);
    if (scene.visual.imageId && !scene.assetIds.includes(scene.visual.imageId))
      throw new Error(`Hero image ${scene.visual.imageId} is not assigned to ${scene.id}`);
    if (scene.visual.imageId && !/\.(png|jpe?g|webp|svg)$/i.test(assets.get(scene.visual.imageId)?.path ?? ''))
      throw new Error(`Hero image ${scene.visual.imageId} must be an image asset`);
    if (scene.sourceIds.length && !fs.existsSync(path.join(folder, 'research.md')))
      throw new Error(`Missing research.md for sourced scene ${scene.id}`);
    for (const id of scene.sourceIds) {
      if (!safeId(id) || !fs.readFileSync(path.join(folder, 'research.md'), 'utf8').includes(`\`${id}\``))
        throw new Error(`Unresolved source ID ${id} in ${scene.id}`);
    }
  }
  if (next !== plan.durationFrames) throw new Error(`Scene coverage ends at ${next}; expected ${plan.durationFrames}`);
  return {plan, manifest};
}
