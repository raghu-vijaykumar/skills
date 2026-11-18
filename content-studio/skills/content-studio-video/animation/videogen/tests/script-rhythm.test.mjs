import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const narration = fileURLToPath(new URL('../scripts/narration.mjs', import.meta.url));

test('rhythm-only narration reviews phrases without synthesizing speech', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'content-studio-rhythm-'));
  try {
    const content = path.join(root, 'content');
    fs.mkdirSync(content);
    fs.writeFileSync(path.join(content, 'video.yaml'), 'content:\n  narration: narration.yaml\n');
    fs.writeFileSync(path.join(content, 'narration.yaml'), [
      'voice: en-US-GuyNeural',
      'phrases:',
      '  - {id: p1, text: "The first valve opens after pressure rises enough."}',
      '  - {id: p2, text: "The second valve closes when the arm returns."}',
      '  - {id: p3, text: "The final switch resets before the cycle repeats."}',
      '',
    ].join('\n'));
    const result = spawnSync(process.execPath, [narration, root, '--rhythm-only'], {
      encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    const reportFile = path.join(root, 'assets', 'generated', 'audio', 'narration-rhythm.json');
    const report = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
    assert.equal(report.mode, 'narration');
    assert.deepEqual(report.observations[0].cue_ids, ['p1', 'p2', 'p3']);
    assert.equal(report.observations[0].kind, 'long_run');
    assert.equal(fs.existsSync(path.join(root, 'assets', 'generated', 'audio', 'narration.mp3')), false);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});

test('cached narration still refreshes the advisory report', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'content-studio-rhythm-cache-'));
  try {
    const content = path.join(root, 'content');
    const audio = path.join(root, 'assets', 'generated', 'audio');
    fs.mkdirSync(content);
    fs.mkdirSync(audio, {recursive: true});
    fs.writeFileSync(path.join(content, 'video.yaml'), 'content:\n  narration: narration.yaml\n');
    const source = 'voice: en-US-GuyNeural\nphrases:\n  - {id: p1, text: "A useful short phrase."}\n';
    fs.writeFileSync(path.join(content, 'narration.yaml'), source);
    fs.writeFileSync(path.join(audio, 'narration.mp3'), 'cached-audio-placeholder');
    const key = crypto.createHash('sha256').update(JSON.stringify({
      version: 4, source, voice: 'en-US-GuyNeural', maxWords: 10,
      globalRate: null, targetWpm: null,
    })).digest('hex');
    fs.writeFileSync(path.join(audio, '.narration-cache.json'), JSON.stringify({
      version: 4, key, timedPhrases: [{id: 'p1', text: 'A useful short phrase.',
        startSeconds: 0, endSeconds: 2}],
    }));
    const result = spawnSync(process.execPath, [narration, root], {encoding: 'utf8'});
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(fs.readFileSync(path.join(audio, 'narration-rhythm.json'), 'utf8'));
    assert.equal(report.passage_count, 1);
    assert.equal(fs.readFileSync(path.join(audio, 'narration.mp3'), 'utf8'), 'cached-audio-placeholder');
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});
