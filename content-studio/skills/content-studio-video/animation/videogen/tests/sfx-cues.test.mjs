import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {validateSfxCues} from '../scripts/validate-sfx-cues.mjs';

const hash = (value) => crypto.createHash('sha256').update(value).digest('hex');

test('Remotion SFX previews stay pending and delivery binds human approval to exact files', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-sfx-'));
  try {
    const video = path.join(root, 'videos', 'demo');
    const content = path.join(video, 'content');
    const publicDir = path.join(root, 'public');
    fs.mkdirSync(content, {recursive: true});
    fs.mkdirSync(path.join(publicDir, 'sfx'), {recursive: true});
    const scene = path.join(video, 'scene-plan.json');
    fs.writeFileSync(scene, JSON.stringify({fps: 30, durationFrames: 90}));
    fs.writeFileSync(path.join(video, 'entry.tsx'),
      '// Content Studio SFX overlay\nconst Root = () => <Composition component={SfxVideo}/>;');
    const bytes = Buffer.from('fixture wav bytes');
    const asset = path.join(publicDir, 'sfx', `${hash(bytes)}.wav`);
    fs.writeFileSync(asset, bytes);
    const cuesFile = path.join(content, 'sfx-cues.json');
    const cataloguePath = path.join(root, 'catalogue.json');
    fs.writeFileSync(cataloguePath, JSON.stringify({assets: [{id: 'sfx-click',
      sha256: hash(bytes), rights: 'licensed', reuse_status: 'reusable',
      effect_review: 'passed', sfx_profile: {identification_review: 'passed'},
      origin: {audit: {status: 'passed'}}}]}));
    const cues = {schema_version: 1, source_sha256: hash(fs.readFileSync(scene)),
      review_status: 'pending_review', clips: [{id: 'sfx-1', kind: 'sfx',
        src: `/sfx/${hash(bytes)}.wav`, sha256: hash(bytes), asset_id: 'sfx-click', start: 1,
        duration: 0.1, volume: 0.4, sound_review_required: true}]};
    fs.writeFileSync(cuesFile, JSON.stringify(cues));
    assert.equal(validateSfxCues(video, publicDir).clips, 1);
    assert.throws(() => validateSfxCues(video, publicDir,
      {delivery: true, cataloguePath}), /listening review/);
    cues.clips[0].sound_review_required = false;
    cues.review_status = 'approved';
    fs.writeFileSync(cuesFile, JSON.stringify(cues));
    fs.writeFileSync(path.join(content, 'sfx-approval.json'), JSON.stringify({actor: 'human',
      reviewer: 'Editor', review_note: 'Listened in picture and approved cue',
      approved_at: '2026-11-18T20:30:00+05:30', cues_sha256: hash(fs.readFileSync(cuesFile))}));
    assert.equal(validateSfxCues(video, publicDir, {delivery: true, cataloguePath}).clips, 1);
    const revoked = JSON.parse(fs.readFileSync(cataloguePath, 'utf8'));
    revoked.assets[0].effect_review = 'pending';
    fs.writeFileSync(cataloguePath, JSON.stringify(revoked));
    assert.throws(() => validateSfxCues(video, publicDir,
      {delivery: true, cataloguePath}), /catalogue listening approval/);
    revoked.assets[0].effect_review = 'passed';
    fs.writeFileSync(cataloguePath, JSON.stringify(revoked));
    fs.writeFileSync(asset, Buffer.from('changed'));
    assert.throws(() => validateSfxCues(video, publicDir, {delivery: true, cataloguePath}), /asset changed/);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});
