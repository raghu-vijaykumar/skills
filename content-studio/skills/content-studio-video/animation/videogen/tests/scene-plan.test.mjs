import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {scaffoldDraft} from '../scripts/scaffold.mjs';
import {validateScenePlan} from '../scripts/scene-plan.mjs';
import {alignmentSegments} from '../scripts/align-narration.mjs';
import {writeScoreWav} from '../scripts/procedural-score.mjs';

const scratch = path.resolve('tmp');
fs.mkdirSync(scratch, {recursive: true});
test('Core Explainer scaffold creates a valid scene contract for portrait and landscape', () => {
  const cwd = fs.mkdtempSync(path.join(scratch, 'explainer-plan-'));
  try {
    fs.writeFileSync(path.join(cwd, 'videogen.config.ts'), 'export default {};\n');
    const config = {videosDir: 'videos', entryPointForVideo: (id) => `videos/${id}/entry.tsx`};
    for (const [id, width, height, durationSeconds] of [
      ['portrait', 1080, 1920, 148.7], ['landscape', 1920, 1080, 300], ['single-frame', 1080, 1920, 1 / 30],
    ]) {
      const result = scaffoldDraft(config, id, {cwd, title: 'A mechanism', width, height, durationSeconds, style: 'core-explainer'});
      const validated = validateScenePlan(result.folder, {width, height, durationInFrames: Math.ceil(durationSeconds * 30)});
      assert.equal(validated.plan.scenes[0].type, 'hero');
      assert.match(fs.readFileSync(path.join(result.folder, 'video.tsx'), 'utf8'), /ExplainerFilm/);
    }
  } finally {
    if (!cwd.startsWith(scratch + path.sep)) throw new Error('Unsafe test cleanup');
    fs.rmSync(cwd, {recursive: true, force: true});
  }
});

test('narration alignment preserves chapter boundaries and limits speedup', () => {
  const scene = {id: 'opening', startFrame: 0, endFrame: 90, narrationCueIds: ['cue-a']};
  const plan = {fps: 30, scenes: [scene]};
  const cues = [{id: 'cue-a', startSeconds: 0, endSeconds: 3.4}];
  assert.equal(alignmentSegments(plan, cues)[0].tempo > 1, true);
  assert.equal(alignmentSegments(plan, [{...cues[0], endSeconds: 2}])[0].tempo, 1);
  assert.throws(() => alignmentSegments(plan, [{...cues[0], id: 'wrong'}]), /mismatch/);
  assert.throws(() => alignmentSegments(plan, [{...cues[0], endSeconds: 9}]), /shorten the script/);
});

test('procedural score is deterministic and exact length', () => {
  const cwd = fs.mkdtempSync(path.join(scratch, 'explainer-score-'));
  try {
    const plan = {fps: 30, durationFrames: 30, scenes: [{startFrame: 0, stateChanges: [{frame: 0}]}]};
    const a = path.join(cwd, 'a.wav'), b = path.join(cwd, 'b.wav');
    assert.equal(writeScoreWav(plan, a, 8000).samples, 8000);
    writeScoreWav(plan, b, 8000);
    assert.deepEqual(fs.readFileSync(a), fs.readFileSync(b));
    assert.equal(fs.statSync(a).size, 44 + 8000 * 2);
  } finally {
    if (!cwd.startsWith(scratch + path.sep)) throw new Error('Unsafe test cleanup');
    fs.rmSync(cwd, {recursive: true, force: true});
  }
});

test('scene plan refuses gaps, unknown types, and reference assets', () => {
  const cwd = fs.mkdtempSync(path.join(scratch, 'explainer-reject-'));
  try {
    fs.writeFileSync(path.join(cwd, 'asset-manifest.json'), '{"schemaVersion":1,"assets":[]}');
    const base = {schemaVersion: 1, width: 1080, height: 1920, fps: 30, durationFrames: 30, scenes: [{
      id: 'scene-one', type: 'hero', startFrame: 0, endFrame: 30, title: 'Teaching', visual: {},
      stateChanges: [{frame: 0, label: 'Start'}], camera: [{frame: 0, scale: 1}],
      assetIds: [], narrationCueIds: [], sourceIds: [], audioCueIds: [],
    }]};
    const write = (plan) => fs.writeFileSync(path.join(cwd, 'scene-plan.json'), JSON.stringify(plan));
    write(base);
    assert.ok(validateScenePlan(cwd));
    write({...base, scenes: [{...base.scenes[0], startFrame: 1}]});
    assert.throws(() => validateScenePlan(cwd), /gap, overlap/);
    write({...base, scenes: [{...base.scenes[0], type: 'unbuilt'}]});
    assert.throws(() => validateScenePlan(cwd), /Unsupported scene/);
    write({...base, scenes: [{...base.scenes[0], stateChanges: [{frame: 10, label: 'Late'}]}]});
    assert.throws(() => validateScenePlan(cwd), /First state change/);
    write({...base, scenes: [{...base.scenes[0], camera: [{frame: 0, scale: 1}, {frame: 0, scale: 1.1}]}]});
    assert.throws(() => validateScenePlan(cwd), /Invalid camera keyframe/);
    write({...base, scenes: [{...base.scenes[0], presenter: {pose: 'unknown'}}]});
    assert.throws(() => validateScenePlan(cwd), /Unsupported presenter pose/);
    write(base);
    fs.mkdirSync(path.join(cwd, 'reference'));
    fs.writeFileSync(path.join(cwd, 'reference', 'frame.png'), 'data');
    const sha256 = crypto.createHash('sha256').update('data').digest('hex');
    fs.writeFileSync(path.join(cwd, 'asset-manifest.json'), JSON.stringify({schemaVersion: 1,
      assets: [{id: 'frame', path: 'reference/frame.png', sha256, origin: 'licensed', license: 'private'}]}));
    assert.throws(() => validateScenePlan(cwd), /reference asset path/);
  } finally {
    if (!cwd.startsWith(scratch + path.sep)) throw new Error('Unsafe test cleanup');
    fs.rmSync(cwd, {recursive: true, force: true});
  }
});

test('scene plan requires imported media provenance and source IDs', () => {
  const cwd = fs.mkdtempSync(path.join(scratch, 'explainer-imports-'));
  try {
    fs.writeFileSync(path.join(cwd, 'asset-manifest.json'), '{"schemaVersion":1,"assets":[]}');
    const plan = {schemaVersion:1,width:1080,height:1920,fps:30,durationFrames:30,
      scenes:[{id:'one',type:'hero',startFrame:0,endFrame:30,title:'Fact',visual:{},
        stateChanges:[{frame:0,label:'Fact'}],camera:[{frame:0,scale:1}],assetIds:[],
        narrationCueIds:[],sourceIds:['primary-one'],audioCueIds:[]}]};
    fs.writeFileSync(path.join(cwd,'scene-plan.json'),JSON.stringify(plan));
    fs.writeFileSync(path.join(cwd,'video.tsx'),"import pic from './art.png';\n");
    assert.throws(()=>validateScenePlan(cwd),/Unlisted media import/);
    fs.writeFileSync(path.join(cwd,'video.tsx'),"import React from 'react';\n");
    assert.throws(()=>validateScenePlan(cwd),/Missing research/);
    fs.writeFileSync(path.join(cwd,'research.md'),'- `primary-one`: https://example.test\n');
    assert.ok(validateScenePlan(cwd));
  } finally {
    if (!cwd.startsWith(scratch + path.sep)) throw new Error('Unsafe test cleanup');
    fs.rmSync(cwd,{recursive:true,force:true});
  }
});
