// Local, source-linked transcription for manually edited exports.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {sha256} from './package.mjs';

function run(executable, args, label) {
  const result = spawnSync(executable, args, {encoding: 'utf8', maxBuffer: 16 * 1024 * 1024});
  if (result.error || result.status !== 0) {
    const tail = `${result.stdout ?? ''}\n${result.stderr ?? ''}`.trim().split(/\r?\n/).slice(-8).join('\n');
    throw new Error(`${label}: ${result.error?.message ?? tail}`);
  }
  return result.stdout;
}
export function probeMaster(file) {
  const data = JSON.parse(run('ffprobe', ['-v','error','-show_entries',
    'format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate',
    '-of','json',file], 'ffprobe'));
  const duration = Number(data.format?.duration);
  if (!Number.isFinite(duration) || duration <= 0 || !data.streams?.some((s) => s.codec_type === 'video') ||
    !data.streams?.some((s) => s.codec_type === 'audio')) throw new Error('Final export needs valid video and audio');
  return {durationSeconds: duration, video: data.streams.find((s) => s.codec_type === 'video'),
    audio: data.streams.find((s) => s.codec_type === 'audio')};
}
function stamp(ms) {
  const total = Math.max(0, Math.round(ms));
  const hours = Math.floor(total / 3600000);
  const minutes = Math.floor(total / 60000) % 60;
  const seconds = Math.floor(total / 1000) % 60;
  return `${String(hours).padStart(2,'0')}:${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')},${String(total % 1000).padStart(3,'0')}`;
}
export function transcriptionSegments(data) {
  const raw = data.transcription ?? data.segments ?? [];
  return raw.map((entry) => ({startMs: Number(entry.offsets?.from ?? entry.start * 1000),
    endMs: Number(entry.offsets?.to ?? entry.end * 1000), text: String(entry.text ?? '').trim()}))
    .filter((entry) => Number.isFinite(entry.startMs) && Number.isFinite(entry.endMs) &&
      entry.endMs > entry.startMs && entry.text);
}
export function toSrt(segments) {
  return segments.map((entry, index) => `${index + 1}\n${stamp(entry.startMs)} --> ${stamp(entry.endMs)}\n${entry.text}\n`).join('\n');
}
export function transcribeDraft(channelRoot, draft, options = {}) {
  const master = path.join(draft, 'video.mp4');
  if (!fs.existsSync(master)) throw new Error('Final manual export video.mp4 is missing');
  const probed = (options.probe ?? probeMaster)(master);
  const execute = options.runCommand ?? run;
  const cache = path.join(channelRoot, 'analysis', 'transcription', path.basename(draft));
  fs.mkdirSync(cache, {recursive: true});
  const audio = path.join(cache, 'audio.wav');
  const prefix = path.join(cache, 'whisper');
  const home = path.join(os.homedir(), '.cache', 'content-studio', 'whisper', 'v1.9.4');
  const cli = options.cli ?? process.env.CONTENT_STUDIO_WHISPER_CLI ?? path.join(home, 'bin', process.platform === 'win32' ? 'whisper-cli.exe' : 'whisper-cli');
  const model = options.model ?? process.env.CONTENT_STUDIO_WHISPER_MODEL ?? path.join(home, 'models', 'ggml-small.bin');
  if (!fs.existsSync(cli) || !fs.existsSync(model)) throw new Error(`Local whisper.cpp v1.9.4 and multilingual small model are required; run setup-whisper.ps1 or set CONTENT_STUDIO_WHISPER_CLI and CONTENT_STUDIO_WHISPER_MODEL`);
  execute('ffmpeg', ['-nostdin','-y','-v','error','-i',master,'-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',audio], 'audio extraction');
  execute(cli, ['-m',model,'-f',audio,'-l','auto','-oj','-of',prefix], 'whisper.cpp transcription');
  const segments = transcriptionSegments(JSON.parse(fs.readFileSync(`${prefix}.json`,'utf8')));
  if (!segments.length) throw new Error('Transcription contained no timed speech; inspect the final export audio');
  const transcript = {model: 'whisper.cpp-v1.9.4-small', masterSha256: sha256(master),
    generatedAt: new Date().toISOString(), durationSeconds: probed.durationSeconds, segments};
  fs.writeFileSync(path.join(draft,'transcript.json'), JSON.stringify(transcript,null,2)+'\n');
  fs.writeFileSync(path.join(draft,'captions.srt'), toSrt(segments));
  for (const portion of [0.1,0.5,0.9]) {
    const at = Math.min(probed.durationSeconds - 0.05, Math.max(0, probed.durationSeconds * portion));
    execute('ffmpeg', ['-nostdin','-y','-v','error','-ss',String(at),'-i',master,'-frames:v','1',
      '-vf','scale=640:-2',path.join(cache,`frame-${Math.round(portion*100)}.png`)], 'reference frame');
  }
  return {transcript: path.join(draft,'transcript.json'), captions: path.join(draft,'captions.srt'),
    frameDir: cache, segments: segments.length, durationSeconds: probed.durationSeconds};
}
