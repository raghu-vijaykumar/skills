import fs from 'node:fs';
import path from 'node:path';

// Canonical draft paths. Keep legacy fallbacks so an unmigrated draft can
// still be inspected, but new writes always target the nested layout.
export function masterFile(draft) {
  const name = path.basename(draft);
  const current = path.join(draft, `${name}-final.mp4`);
  const legacyFinal = path.join(draft, 'final-video.mp4');
  const legacyVideo = path.join(draft, 'video', 'with-audio.mp4');
  const legacy = path.join(draft, 'video.mp4');
  if (fs.existsSync(current)) return current;
  for (const candidate of [legacyFinal, legacyVideo, legacy]) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return current;
}

export function silentFile(draft) {
  return path.join(draft, '.content-studio', 'silent.mp4');
}

export function musicFile(draft) {
  return path.join(draft, `${path.basename(draft)}-final-with-music.mp4`);
}

export function transcriptFile(draft) {
  return path.join(draft, 'transcript.json');
}

export function captionsFile(draft) {
  return path.join(draft, 'captions.srt');
}

export function titleFile(draft) {
  return path.join(draft, 'title.txt');
}

export function descriptionFile(draft) {
  return path.join(draft, 'description.txt');
}

export function checklistFile(draft) {
  return path.join(draft, 'lifecycle-checklist.json');
}
