// One file-hash approval contract for edited and code-rendered video packages.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parse} from 'yaml';
import {selectMaster} from '../skills/content-studio-videogen/scripts/publish-youtube.mjs';

export function readJson(file) { return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {}; }
export function sha256(file) {
  const digest = createHash('sha256');
  const fd = fs.openSync(file, 'r');
  try {
    const block = Buffer.alloc(1024 * 1024);
    let count;
    while ((count = fs.readSync(fd, block, 0, block.length, null)) > 0) digest.update(block.subarray(0, count));
  } finally { fs.closeSync(fd); }
  return digest.digest('hex');
}
export function packageFiles(draft, id) {
  const title = path.join(draft, 'title.txt');
  const description = path.join(draft, 'description.txt');
  const thumbnail = ['thumbnail.png', 'thumbnail.jpg', 'thumbnail.jpeg']
    .map((name) => path.join(draft, name)).find((file) => fs.existsSync(file));
  if (!fs.existsSync(title) || !fs.existsSync(description)) throw new Error('title.txt and description.txt are required');
  const master = selectMaster(draft, id);
  const videoYaml = path.join(draft, 'content', 'video.yaml');
  const caption = path.join(draft, 'instagram-caption.txt');
  const creative = path.join(draft, 'creative.json');
  const transcript = path.join(draft, 'transcript.json');
  const subtitles = path.join(draft, 'captions.srt');
  return {title, description, ...(thumbnail ? {thumbnail} : {}), master,
    ...(fs.existsSync(creative) ? {creative} : {}),
    ...(fs.existsSync(transcript) ? {transcript} : {}),
    ...(fs.existsSync(subtitles) ? {subtitles} : {}),
    ...(fs.existsSync(videoYaml) ? {videoYaml} : {}),
    ...(fs.existsSync(caption) ? {caption} : {})};
}
export function fingerprint(files) {
  return Object.fromEntries(Object.entries(files).map(([key, file]) => [key, sha256(file)]));
}
export function validateSrt(file, durationSeconds = null) {
  const blocks = fs.readFileSync(file, 'utf8').trim().split(/\r?\n\s*\r?\n/);
  let previousEnd = -1;
  const clock = (value) => {
    const match = value.match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/);
    return match ? Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]) + Number(match[4]) / 1000 : NaN;
  };
  if (!blocks.length) throw new Error('captions.srt is empty');
  for (const block of blocks) {
    const lines = block.split(/\r?\n/);
    const times = lines[1]?.match(/^(\S+) --> (\S+)$/);
    const start = clock(times?.[1] ?? '');
    const end = clock(times?.[2] ?? '');
    if (!/^\d+$/.test(lines[0] ?? '') || !Number.isFinite(start) || !Number.isFinite(end) ||
        start < previousEnd || end <= start || (durationSeconds && end > durationSeconds + 0.1) ||
        !lines.slice(2).join(' ').trim()) throw new Error('captions.srt has invalid timing or empty text');
    previousEnd = end;
  }
  return blocks.length;
}
export function validateDraftRecord(draft, files) {
  const manifest = readJson(path.join(draft, 'draft.json'));
  const creative = readJson(path.join(draft, 'creative.json'));
  if (!files.creative || !creative.themeId || !creative.styleId || !creative.format ||
      !creative.renderer || !Array.isArray(creative.choices))
    throw new Error('creative.json needs themeId, styleId, format, renderer, and choices');
  const kind = manifest.production?.kind ?? (files.videoYaml ? 'remotion' : 'edited');
  if (!['edited', 'remotion'].includes(kind)) throw new Error('Unknown draft production kind');
  if (kind === 'edited' && files.transcript) {
    const transcript = readJson(files.transcript);
    const noSpeech = transcript.speech === false;
    if (transcript.masterSha256 !== sha256(files.master) || !Array.isArray(transcript.segments) ||
        (noSpeech && transcript.segments.length) || (!noSpeech && !transcript.segments.length))
      throw new Error('Edited export transcript/captions do not match this master');
    if (!noSpeech) {
      if (!files.subtitles) throw new Error('Edited export needs captions.srt');
      validateSrt(files.subtitles, transcript.durationSeconds);
    }
  }
  return {kind, creative};
}
export function validateChecklist(draft, phase = 'pre_publish') {
  if (!['pre_publish', 'all'].includes(phase)) throw new Error(`Unknown checklist phase: ${phase}`);
  const manifest = readJson(path.join(draft, 'draft.json'));
  const file = path.join(draft, 'lifecycle-checklist.json');
  if (!fs.existsSync(file)) {
    if (manifest.lifecycle === 'main')
      throw new Error('Main lifecycle draft requires lifecycle-checklist.json');
    return null;
  }
  let data;
  try {
    data = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    throw new Error('lifecycle-checklist.json is not valid JSON');
  }
  if (!Array.isArray(data.items) || !data.items.length)
    throw new Error('lifecycle-checklist.json has no items');
  const selected = phase === 'pre_publish'
    ? data.items.filter((item) => item.phase === 'pre_publish')
    : data.items;
  if (!selected.length) throw new Error(`lifecycle-checklist.json has no ${phase} items`);
  const failures = [];
  for (const item of selected) {
    const id = item.id ?? '?';
    if (item.status === 'done') {
      if (!(Array.isArray(item.evidence) && item.evidence.length) && !String(item.note ?? '').trim())
        failures.push(`${id}: done without evidence or note`);
    } else if (item.status === 'not_applicable') {
      if (!String(item.reason ?? '').trim()) failures.push(`${id}: not_applicable without reason`);
    } else if (item.status === 'deferred') {
      failures.push(`${id}: deferred`);
    } else {
      failures.push(`${id}: ${item.status ?? 'pending'}`);
    }
  }
  if (failures.length) throw new Error(`Lifecycle checklist incomplete: ${failures.join(', ')}`);
  return data;
}
export function approvePackage(draft, id, note) {
  if (!note?.trim()) throw new Error('Approval note is required after human review');
  const files = packageFiles(draft, id);
  if (!files.thumbnail) throw new Error('An approved thumbnail is required');
  validateDraftRecord(draft, files);
  validateChecklist(draft, 'pre_publish');
  const approval = {approvedAt: new Date().toISOString(), note: note.trim(), files: fingerprint(files)};
  fs.writeFileSync(path.join(draft, 'package-approval.json'), JSON.stringify(approval, null, 2) + '\n');
  return approval;
}
export function verifyPackage(draft, id) {
  const approved = readJson(path.join(draft, 'package-approval.json'));
  if (!approved.approvedAt || !approved.files) throw new Error('Human-reviewed package approval is missing');
  const files = packageFiles(draft, id);
  validateDraftRecord(draft, files);
  validateChecklist(draft, 'pre_publish');
  const current = fingerprint(files);
  for (const [name, hash] of Object.entries(current)) {
    if (approved.files[name] !== hash) throw new Error(`${name} changed since package approval`);
  }
  for (const name of Object.keys(approved.files)) {
    if (!current[name]) throw new Error(`${name} disappeared since package approval`);
  }
  return {files, approval: approved};
}
export function itemFromDraft(draft, id) {
  const files = packageFiles(draft, id);
  const title = fs.readFileSync(files.title, 'utf8').trim();
  const description = fs.readFileSync(files.description, 'utf8').trimEnd();
  const videoYaml = path.join(draft, 'content', 'video.yaml');
  const authored = fs.existsSync(videoYaml) ? parse(fs.readFileSync(videoYaml, 'utf8')) : {};
  const manifest = readJson(path.join(draft, 'draft.json'));
  return {dir: draft, compositionId: authored.video?.compositionId ?? null,
    kind: manifest.production?.kind ?? (authored.video?.compositionId ? 'remotion' : 'edited'),
    value: {...authored, video: {...authored.video, id, title, description},
      publishing: {...authored.publishing,
        youtube: {...authored.publishing?.youtube, title, description},
        instagram: {...authored.publishing?.instagram,
          caption: fs.existsSync(path.join(draft, 'instagram-caption.txt')) ?
            fs.readFileSync(path.join(draft, 'instagram-caption.txt'), 'utf8').trim() :
            authored.publishing?.instagram?.caption || description}}}};
}
