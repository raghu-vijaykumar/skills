// Lock generated speech phrases to authored scene boundaries without replacing the script.
// Faster phrases are padded with silence; only overlong phrases are gently accelerated.
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {validateScenePlan} from './scene-plan.mjs';

const sha256 = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const seconds = (frame, fps) => frame / fps;
export function alignmentSegments(plan, cues) {
  if (plan.scenes.length !== cues.length) throw new Error('One narration cue per scene is required for alignment');
  return plan.scenes.map((scene, i) => {
    const cue = cues[i];
    if (scene.narrationCueIds.length !== 1 || scene.narrationCueIds[0] !== cue.id)
      throw new Error(`Narration cue mismatch in ${scene.id}`);
    const duration = seconds(scene.endFrame - scene.startFrame, plan.fps);
    const original = cue.endSeconds - cue.startSeconds;
    if (!(duration > 0 && original > 0)) throw new Error(`Invalid narration duration in ${scene.id}`);
    const tempo = Math.max(1, original / Math.max(0.1, duration - 0.08));
    if (tempo > 1.7) throw new Error(`${scene.id} speech exceeds scene by too much (${tempo.toFixed(2)}x); shorten the script`);
    return {id: scene.id, cue, start: seconds(scene.startFrame, plan.fps), duration, tempo};
  });
}

function run(exe, args) {
  const result = spawnSync(exe, args, {encoding: 'utf8', maxBuffer: 4 * 1024 * 1024});
  if (result.error || result.status !== 0) throw new Error(`${exe}: ${(result.stderr || result.error?.message || '').trim().split('\n').slice(-6).join('\n')}`);
}

export function alignNarration(folder) {
  const checked = validateScenePlan(folder);
  if (!checked) throw new Error('scene-plan.json is required');
  const {plan} = checked;
  const audioDir = path.join(folder, 'assets', 'generated', 'audio');
  const audio = path.join(audioDir, 'narration.mp3');
  const original = path.join(audioDir, '.narration-original.mp3');
  const cacheFile = path.join(audioDir, '.narration-cache.json');
  const cueFile = path.join(folder, 'assets', 'generated', 'narration.ts');
  for (const file of [audio, cacheFile, cueFile]) if (!fs.existsSync(file)) throw new Error(`Missing ${file}; run videogen narration`);
  const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
  // A fresh narration run drops alignment metadata; refresh the original in that case.
  if (!cache.alignment || !fs.existsSync(original)) fs.copyFileSync(audio, original);
  if (cache.alignment?.originalAudioSha256 && sha256(original) !== cache.alignment.originalAudioSha256)
    throw new Error('Original narration cache changed; regenerate speech before alignment');
  const segments = alignmentSegments(plan, cache.alignment?.originalCues ?? cache.timedPhrases);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'videogen-align-'));
  try {
    const files = [];
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i], out = path.join(tmp, `${String(i).padStart(3,'0')}.wav`);
      const filter = `atrim=start=${seg.cue.startSeconds}:end=${seg.cue.endSeconds},asetpts=PTS-STARTPTS,atempo=${seg.tempo},apad,atrim=duration=${seg.duration}`;
      run('ffmpeg', ['-y','-hide_banner','-loglevel','error','-i',original,'-af',filter,'-ar','48000','-ac','1','-c:a','pcm_s16le',out]);
      files.push(out);
    }
    const list = path.join(tmp, 'concat.txt');
    fs.writeFileSync(list, files.map((file) => `file '${file.replaceAll("'", "'\\''")}'`).join('\n') + '\n');
    const aligned = path.join(tmp, 'aligned.mp3');
    run('ffmpeg', ['-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',list,'-c:a','libmp3lame','-b:a','192k',aligned]);
    const probed = spawnSync('ffprobe', ['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',aligned], {encoding:'utf8'});
    const duration = Number(probed.stdout?.trim());
    if (probed.status !== 0 || Math.abs(duration - seconds(plan.durationFrames,plan.fps)) > 0.08)
      throw new Error(`Aligned narration duration ${duration} differs from scene plan`);
    const originals = cache.alignment?.originalCues ?? cache.timedPhrases;
    const timedPhrases = segments.map((seg, i) => ({...originals[i], startSeconds: seg.start,
      endSeconds: seg.start + seg.duration, audioDurationSeconds: seg.duration}));
    fs.copyFileSync(aligned, audio);
    cache.timedPhrases = timedPhrases;
    cache.audioDurationSeconds = seconds(plan.durationFrames, plan.fps);
    cache.alignment = {scenePlanSha256: sha256(path.join(folder,'scene-plan.json')),
      originalAudioSha256: sha256(original), originalCues: originals, method: 'speed-overlong-and-pad-short', version: 1};
    fs.writeFileSync(cacheFile, JSON.stringify(cache,null,2)+'\n');
    fs.writeFileSync(cueFile, `// GENERATED FILE. DO NOT EDIT.\nexport const narrationCues = ${JSON.stringify(timedPhrases,null,2)} as const;\n`);
    return {duration, scenes: segments.length, maxTempo: Math.max(...segments.map((s)=>s.tempo))};
  } finally {
    fs.rmSync(tmp, {recursive: true, force: true});
  }
}
