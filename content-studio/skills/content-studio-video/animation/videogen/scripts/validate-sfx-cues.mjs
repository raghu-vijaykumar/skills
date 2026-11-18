// Keep generated Remotion SFX cues tied to the authored scene plan and exact WAVs.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const digest = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

export function validateSfxCues(videoDir, publicDir, {delivery = false, cataloguePath} = {}) {
  const file = path.join(videoDir, 'content', 'sfx-cues.json');
  if (!fs.existsSync(file)) return null;
  const cues = JSON.parse(fs.readFileSync(file, 'utf8'));
  const plan = path.join(videoDir, 'scene-plan.json');
  if (!fs.existsSync(plan) || cues.schema_version !== 1 || cues.source_sha256 !== digest(plan) || !Array.isArray(cues.clips))
    throw new Error('SFX cues are stale or malformed for this scene plan');
  const entry = path.join(videoDir, 'entry.tsx');
  if (!fs.existsSync(entry) || !fs.readFileSync(entry, 'utf8').includes('component={SfxVideo}') ||
      !fs.readFileSync(entry, 'utf8').includes('Content Studio SFX overlay'))
    throw new Error('SFX cues are not mounted in the video composition');
  const scenePlan = JSON.parse(fs.readFileSync(plan, 'utf8'));
  const duration = scenePlan.durationFrames / scenePlan.fps;
  const ids = new Set();
  const catalogue = delivery ? JSON.parse(fs.readFileSync(cataloguePath ??
    path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../stock-library/assets/catalogue.json'),
  'utf8')).assets : [];
  for (const clip of cues.clips) {
    if (clip.kind !== 'sfx' || typeof clip.id !== 'string' || ids.has(clip.id) ||
        !/^\/sfx\/[a-f0-9]{64}\.wav$/.test(clip.src ?? '') ||
        !Number.isFinite(clip.start) || clip.start < 0 ||
        !Number.isFinite(clip.duration) || clip.duration <= 0 || clip.start + clip.duration > duration + .02 ||
        !Number.isFinite(clip.volume) || clip.volume < 0 || clip.volume > 1)
      throw new Error(`Invalid SFX clip: ${clip.id}`);
    ids.add(clip.id);
    const asset = path.join(publicDir, clip.src.slice(1));
    if (!fs.existsSync(asset) || digest(asset) !== clip.sha256)
      throw new Error(`SFX asset changed: ${clip.id}`);
    if (delivery) {
      if (clip.sound_review_required) throw new Error(`SFX needs listening review: ${clip.id}`);
      const item = catalogue.find((row) => row.id === clip.asset_id);
      if (!item || item.sha256 !== clip.sha256 || item.origin?.audit?.status !== 'passed' ||
          item.rights === 'unknown' || item.reuse_status !== 'reusable' ||
          item.effect_review !== 'passed' || item.sfx_profile?.identification_review !== 'passed')
        throw new Error(`SFX lacks current catalogue listening approval: ${clip.id}`);
    }
  }
  if (delivery) {
    const approvalFile = path.join(videoDir, 'content', 'sfx-approval.json');
    if (!fs.existsSync(approvalFile)) throw new Error('Human SFX approval is missing');
    const approval = JSON.parse(fs.readFileSync(approvalFile, 'utf8'));
    if (cues.review_status !== 'approved' || approval.actor !== 'human' ||
        !approval.reviewer || !approval.review_note || !approval.approved_at ||
        approval.cues_sha256 !== digest(file)) throw new Error('Human SFX approval is stale or incomplete');
  }
  return {file, clips: cues.clips.length, review_status: cues.review_status};
}
