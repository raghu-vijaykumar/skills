import * as fs from "node:fs";
import * as path from "node:path";
import * as url from "node:url";
import { validateCamera, rectInView } from "@raghu-vijaykumar/videogen/runtime/animation/camera";
import { resolveFrame, pathCollisionReport, cameraContinuityReport } from "@raghu-vijaykumar/videogen/runtime/animation/frameState";
import { validateMedia } from "@raghu-vijaykumar/videogen/runtime/animation/media";
const video = process.argv[2];
if (!video) {
  console.error("Usage: node scripts/check-motion.mts <video-id>");
  process.exit(1);
}
const root = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? "videos", video);
if (!fs.existsSync(root)) {
  console.error(`Video not found: videos/${video}`);
  process.exit(1);
}
const narrationPath = path.resolve(root, "assets/generated/narration.ts");
if (!fs.existsSync(narrationPath)) {
  console.error(`No generated narration: ${narrationPath}`);
  process.exit(1);
}
const src = fs.readFileSync(narrationPath, "utf8");
const match = src.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
if (!match) {
  console.error(`Could not parse narration cues: ${narrationPath}`);
  process.exit(1);
}
const cues = JSON.parse(match[1]);
const timelinePath = path.resolve(root, "timeline.ts");
if (!fs.existsSync(timelinePath)) {
  console.log(`Motion check: ${video} skipped (no timeline.ts)`);
  process.exit(0);
}
const timelineSrc = fs.readFileSync(timelinePath, "utf8");
if (!/motionSource/.test(timelineSrc)) {
  console.log(`Motion check: ${video} skipped (no motionSource record \u2014 legacy frame-based video)`);
  process.exit(0);
}
let motionSource;
let timelineModule = null;
try {
  timelineModule = await import(url.pathToFileURL(timelinePath).href);
  if (typeof timelineModule.motionSource !== "function") {
    console.error(`timeline.ts must export motionSource(cues) to declare a motion record.`);
    process.exit(1);
  }
  motionSource = timelineModule.motionSource(cues);
} catch (error) {
  console.error(`Motion check: failed to load motion record for ${video}`);
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
const events = [...motionSource.events].sort((a, b) => a.t - b.t);
const rests = (motionSource.rests ?? []).sort((a, b) => a.start - b.start);
const issues = [];
function unionLength(segments) {
  if (segments.length === 0) return 0;
  const sorted = segments.slice().sort((a, b) => a.start - b.start);
  let total = 0;
  let cur = sorted[0];
  for (const seg of sorted.slice(1)) {
    if (seg.start <= cur.end) cur.end = Math.max(cur.end, seg.end);
    else {
      total += cur.end - cur.start;
      cur = seg;
    }
  }
  total += cur.end - cur.start;
  return total;
}
function coverage(start, end) {
  const segs = [];
  for (const e of events) {
    const s = Math.max(e.t, start);
    const en = Math.min(e.t + e.duration, end);
    if (en > s) segs.push({ start: s, end: en });
  }
  for (const r of rests) {
    const s = Math.max(r.start, start);
    const en = Math.min(r.end, end);
    if (en > s) segs.push({ start: s, end: en });
  }
  return unionLength(segs);
}
const MIN_LONG = 2.2;
const LONG_MIN_COVERAGE = 0.45;
const MIN_MEDIUM = 1.4;
const MEDIUM_MIN_COVERAGE = 0.25;
for (const cue of cues) {
  const dur = cue.endSeconds - cue.startSeconds;
  if (dur < MIN_MEDIUM) continue;
  const need = dur >= MIN_LONG ? dur * LONG_MIN_COVERAGE : dur * MEDIUM_MIN_COVERAGE;
  const got = coverage(cue.startSeconds, cue.endSeconds);
  if (got < need - 1e-6) {
    issues.push({
      t: cue.startSeconds,
      kind: "error",
      msg: `phrase "${cue.text}" is ${dur.toFixed(1)}s long but only ${(got / dur * 100).toFixed(0)}% has motion (need >= ${(need / dur * 100).toFixed(0)}%). Add a visible beat or a deliberate rest.`
    });
  }
  if (dur >= 3) {
    const starts = events.filter((e) => e.t >= cue.startSeconds && e.t < cue.endSeconds).length;
    if (starts === 0) {
      issues.push({
        t: cue.startSeconds,
        kind: "warn",
        msg: `phrase "${cue.text}" has no new beat inside it (coverage comes from inherited/long motion only).`
      });
    }
  }
}
const MIN_DWELL = {
  mark: 0.3,
  count: 0.4,
  highlight: 0.4,
  draw: 0.3,
  reveal: 0.3,
  visit: 0.25
};
for (const e of events) {
  const min = MIN_DWELL[e.kind];
  if (min && e.duration + 1e-6 < min) {
    issues.push({
      t: e.t,
      kind: "error",
      msg: `${e.kind} on "${e.target ?? "?"}" only lasts ${e.duration.toFixed(2)}s (min ${min.toFixed(2)}s) \u2014 not readable.`
    });
  }
}
const step = Number(process.argv[3] ?? "0.5");
const duration = cues[cues.length - 1]?.endSeconds ?? 0;
for (let t = 0; t <= duration + 1e-9; t += step) {
  const primary = events.filter((e) => e.attention === "primary" && t >= e.t && t < e.t + e.duration);
  if (primary.length > 2) {
    issues.push({
      t,
      kind: "warn",
      msg: `${primary.length} primary-attention events active at once (${primary.map((p) => `${p.kind}:${p.target ?? "?"}`).join(", ")})`
    });
    if (t + step <= t) break;
  }
}
if (timelineModule && typeof timelineModule.cameraProgram === "function") {
  try {
    const program = timelineModule.cameraProgram(cues);
    const camIssues = validateCamera(program.shots, program.width, program.height);
    for (const camIssue of camIssues) {
      if (camIssue.kind === "error") {
        issues.push({ t: camIssue.t, kind: "error", msg: `camera "${camIssue.shot}": ${camIssue.msg}` });
      }
    }
    for (const shot of program.shots) {
      if (!shot.region) continue;
      const last = shot.keys[shot.keys.length - 1];
      const cam = { cx: last.cx, cy: last.cy, scale: last.scale };
      if (!rectInView(shot.region, cam, program.width, program.height)) {
        issues.push({ t: last.t, kind: "error", msg: `camera "${shot.id}" loses its region in viewer space` });
      }
    }
  } catch (error) {
    issues.push({ t: 0, kind: "error", msg: `camera program failed: ${error instanceof Error ? error.message : String(error)}` });
  }
}
if (timelineModule && typeof timelineModule.frameProgram === "function") {
  try {
    const program = timelineModule.frameProgram(cues);
    for (let t = 0; t <= duration + 1e-9; t += 1) {
      const inputs = {
        t,
        width: program.width,
        height: program.height,
        shots: program.shots,
        geometry: program.geometry,
        paths: program.paths
      };
      const frame = resolveFrame(inputs);
      for (const issue of pathCollisionReport(frame, inputs)) {
        issues.push({ t: issue.t, kind: issue.kind, msg: issue.msg });
      }
    }
    if (Array.isArray(program.shots) && program.shots.length > 0) {
      for (const issue of cameraContinuityReport(program.shots, program.width, program.height)) {
        issues.push({ t: issue.t, kind: issue.kind, msg: issue.msg });
      }
    }
  } catch (error) {
    issues.push({ t: 0, kind: "error", msg: `frame program failed: ${error instanceof Error ? error.message : String(error)}` });
  }
}
if (timelineModule && typeof timelineModule.mediaSource === "function") {
  try {
    const clips = timelineModule.mediaSource(cues);
    for (const issue of validateMedia(clips)) {
      issues.push({ t: issue.t, kind: issue.kind, msg: `media "${issue.clip}": ${issue.msg}` });
    }
  } catch (error) {
    issues.push({ t: 0, kind: "error", msg: `media source failed: ${error instanceof Error ? error.message : String(error)}` });
  }
}
const errors = issues.filter((i) => i.kind === "error");
const warns = issues.filter((i) => i.kind === "warn");
console.log(`
Motion audit: ${video}, ${cues.length} phrases, ${events.length} events, ${duration.toFixed(1)}s`);
if (issues.length === 0) {
  console.log("  \u2713 No motion issues");
} else {
  console.log(`  \u2717 errors=${errors.length}  \u26A0 warnings=${warns.length}`);
  const shown = /* @__PURE__ */ new Set();
  for (const issue of [...errors, ...warns]) {
    const key = issue.msg;
    if (shown.has(key)) continue;
    shown.add(key);
    console.log(`  [${issue.kind === "error" ? "\u2717" : "\u26A0"}] t=${issue.t.toFixed(1)}s ${issue.msg}`);
  }
}
process.exit(errors.length > 0 ? 1 : 0);
