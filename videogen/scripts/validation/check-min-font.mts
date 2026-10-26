// Minimum-content-font audit for shorts that opt in via content/video.yaml:
//
//   content:
//     narration: narration.yaml
//     minTextFontSize: 26
//
// When `content.minTextFontSize` is set, every literal `fontSize: N` / `fontSize=N`
// in the video's authored visuals/components/stage sources must be >= that floor,
// so on-screen text stays readable at phone scale. Finished legacy videos that
// do not declare the field are skipped (they keep their own typography rules).
//
// Usage: node scripts/check-min-font.mts <video-id> [floor]

import * as fs from 'node:fs';
import * as path from 'node:path';
import {parse} from 'yaml';

const video = process.argv[2];
if (!video) {
  console.error('Usage: node scripts/check-min-font.mts <video-id>');
  process.exit(1);
}
const root = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', video);
if (!fs.existsSync(root)) {
  console.error(`Video not found: videos/${video}`);
  process.exit(1);
}

const metaPath = path.join(root, 'content', 'video.yaml');
let floor = Number(process.argv[3]);
if (!Number.isFinite(floor)) {
  floor = null;
  if (fs.existsSync(metaPath)) {
    try {
      const meta = parse(fs.readFileSync(metaPath, 'utf8'));
      const declared = meta?.content?.minTextFontSize;
      if (Number.isFinite(declared) && Number(declared) > 0) floor = Number(declared);
    } catch {
      floor = null;
    }
  }
}
if (floor === null) {
  console.log(`Min-font check: ${video} skipped (no content.minTextFontSize in video.yaml)`);
  process.exit(0);
}

// Scan authored sources (visuals/components/stage), not generated assets.
const dirs = ['visuals', 'components'];
const files: string[] = [];
for (const d of dirs) {
  const abs = path.join(root, d);
  if (!fs.existsSync(abs)) continue;
  const walk = (p: string) => {
    for (const e of fs.readdirSync(p, {withFileTypes: true})) {
      const full = path.join(p, e.name);
      if (e.isDirectory()) walk(full);
      else if (/\.(ts|tsx)$/.test(e.name)) files.push(full);
    }
  };
  walk(abs);
}
for (const f of ['stage.tsx', 'video.tsx']) {
  const p = path.join(root, f);
  if (fs.existsSync(p)) files.push(p);
}

const sizeRe = /fontSize\s*(?::|=)\s*\{?\s*(\d+)\s*\}?/g;
const errors: string[] = [];
for (const file of files.sort()) {
  const src = fs.readFileSync(file, 'utf8');
  const lines = src.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    sizeRe.lastIndex = 0;
    let m;
    while ((m = sizeRe.exec(line)) !== null) {
      const n = Number(m[1]);
      if (n < floor) {
        const rel = path.relative(root, file);
        errors.push(`${rel}:${i + 1}: fontSize ${n}px < floor ${floor}px  ->  ${line.trim().slice(0, 120)}`);
      }
    }
  }
}

if (errors.length > 0) {
  console.error(`\nMIN-FONT VALIDATION FAILED for ${video} (floor ${floor}px)`);
  for (const e of errors) console.error(`  ✗ ${e}`);
  console.error(`Raise these font sizes or remove content.minTextFontSize if they are intentional.`);
  process.exit(1);
}
console.log(`Min-font OK: ${video} (floor ${floor}px)`);
