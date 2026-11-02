// Verify that derived audio and cue timing still correspond to the authored YAML.
// Version 3 caches remain valid for unchanged legacy films that were approved
// at their original voice pace; new narration uses the current generator.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {parse} from 'yaml';

const root = path.resolve(process.argv[2] ?? '');
function fail(message) {throw new Error(`Narration verification: ${message}`);}
const metadata = parse(fs.readFileSync(path.join(root, 'content', 'video.yaml'), 'utf8'));
const sourceFile = path.resolve(root, 'content', metadata.content?.narration ?? 'narration.yaml');
const source = fs.readFileSync(sourceFile, 'utf8').replace(/\r/g, '');
const authored = parse(source);
const audioFile = path.join(root, 'assets', 'generated', 'audio', 'narration.mp3');
const cacheFile = path.join(root, 'assets', 'generated', 'audio', '.narration-cache.json');
const cueFile = path.join(root, 'assets', 'generated', 'narration.ts');
for (const file of [audioFile, cacheFile, cueFile]) if (!fs.existsSync(file)) fail(`missing ${file}; run videogen narration`);
const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
const voice = authored.voice ?? 'en-US-GuyNeural';
const maxWords = authored.max_words_per_phrase ?? 10;
const globalRate = authored.rate ?? null;
const targetWpm = authored.wpm ?? null;
const legacy = cache.version === 3;
if (![3, 4].includes(cache.version)) fail(`unsupported cache version ${cache.version}; run videogen narration`);
if (legacy && (globalRate || targetWpm || authored.phrases?.some((phrase) => phrase.rate || phrase.pause))) fail('legacy audio cannot use rate or pause overrides; run videogen narration');
const payload = legacy
  ? {version: 3, source, voice, maxWords}
  : {version: 4, source, voice, maxWords, globalRate, targetWpm};
const expected = crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
if (cache.key !== expected) fail('authored narration changed since audio generation; run videogen narration');
if (!Array.isArray(cache.timedPhrases) || cache.timedPhrases.length !== authored.phrases?.length) fail('cached cue count disagrees with narration YAML');
const match = fs.readFileSync(cueFile, 'utf8').match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
if (!match) fail(`cannot parse ${cueFile}`);
const cues = JSON.parse(match[1]);
if (JSON.stringify(cues) !== JSON.stringify(cache.timedPhrases)) fail('generated cues differ from the approved audio cache');
for (const [index, cue] of cues.entries()) {
  const phrase = authored.phrases[index];
  const words = String(phrase.text ?? '').trim().replace(/\s+/g, ' ').split(/\s+/).filter(Boolean);
  if (cue.id !== phrase.id || cue.text !== words.join(' ') || words.length > maxWords) fail(`phrase ${index + 1} differs from its generated cue`);
  if (!Number.isFinite(cue.startSeconds) || !Number.isFinite(cue.endSeconds) || cue.endSeconds <= cue.startSeconds) fail(`invalid cue timing at phrase ${index + 1}`);
  if (index > 0 && cue.startSeconds < cues[index - 1].endSeconds - 0.01) fail(`overlapping cue timing at phrase ${index + 1}`);
}
const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=sample_rate:format=duration', '-of', 'json', audioFile], {encoding: 'utf8'});
if (probe.error || probe.status !== 0) fail(`cannot probe narration audio: ${probe.stderr ?? probe.error?.message}`);
const info = JSON.parse(probe.stdout);
const duration = Number(info.format?.duration);
const sampleRate = Number(info.streams?.[0]?.sample_rate);
// MP3 phrase concatenation can add one encoder frame per phrase to the final
// container. Bound that padding by the encoded frame duration rather than a
// fixed small tolerance that falsely rejects longer narration assemblies.
const frameSeconds = 1152 / sampleRate;
const padLimit = (cues.length + 2) * frameSeconds;
const cueEnd = Number(cache.audioDurationSeconds);
if (!Number.isFinite(duration) || !Number.isFinite(frameSeconds) || duration < cueEnd - frameSeconds || duration > cueEnd + padLimit) fail('audio duration differs from the cue cache beyond MP3 frame padding');
console.log(`Narration verified: ${cues.length} cues, ${duration.toFixed(2)}s${legacy ? ' (approved legacy pace)' : ''}`);
