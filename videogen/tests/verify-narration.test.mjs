import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const verifier = fileURLToPath(new URL('../scripts/verify-narration.mjs', import.meta.url));
test('narration cache accepts matching audio and rejects changed source text', () => {
  const root = fs.mkdtempSync(path.join(process.cwd(), 'videogen-test-'));
  try {
    const contentDir = path.join(root, 'content');
    const audioDir = path.join(root, 'assets', 'generated', 'audio');
    fs.mkdirSync(contentDir, {recursive: true});
    fs.mkdirSync(audioDir, {recursive: true});
    fs.writeFileSync(path.join(contentDir, 'video.yaml'), 'content:\n  narration: narration.yaml\n');
    const source = 'voice: en-US-GuyNeural\nphrases:\n  - {id: phrase-1, text: "A test phrase."}\n';
    fs.writeFileSync(path.join(contentDir, 'narration.yaml'), source);
    const audioFile = path.join(audioDir, 'narration.mp3');
    const encoded = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1', '-q:a', '9', '-acodec', 'libmp3lame', audioFile], {encoding: 'utf8'});
    assert.equal(encoded.status, 0, encoded.stderr);
    const probed = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audioFile], {encoding: 'utf8'});
    assert.equal(probed.status, 0, probed.stderr);
    const duration = Number(probed.stdout.trim());
    const cues = [{id: 'phrase-1', text: 'A test phrase.', startSeconds: 0, endSeconds: duration}];
    fs.writeFileSync(path.join(root, 'assets', 'generated', 'narration.ts'), `export const narrationCues = ${JSON.stringify(cues)} as const;\n`);
    const key = crypto.createHash('sha256').update(JSON.stringify({version: 4, source, voice: 'en-US-GuyNeural', maxWords: 10, globalRate: null, targetWpm: null})).digest('hex');
    fs.writeFileSync(path.join(audioDir, '.narration-cache.json'), JSON.stringify({version: 4, key, audioDurationSeconds: duration, timedPhrases: cues}));
    const verify = () => spawnSync(process.execPath, [verifier, root], {encoding: 'utf8'});
    assert.equal(verify().status, 0);
    fs.writeFileSync(path.join(contentDir, 'narration.yaml'), source.replace('A test phrase.', 'A changed phrase.'));
    const stale = verify();
    assert.notEqual(stale.status, 0);
    assert.match(stale.stderr, /authored narration changed/);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});
