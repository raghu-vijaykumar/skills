// Reusable camera movement primitives built on the existing deterministic
// camera system (camera.ts). Every function returns a regular CameraShot
// resolved by cameraTransformAt — no second camera abstraction, no new state.
//
// Primitives are opt-in: existing videos keep their shots untouched. Each
// movement supports:
//   - a focal target (region or point in canvas space)
//   - a duration
//   - an intensity (0..1+ ; 1 is the "textbook" move, >1 overshoots)
//   - an easing
//   - composition: pass `opts.from` (the previous camera transform) to start
//     exactly where the previous shot ends; sequenceShots() does this for whole
//     programs so segment boundaries never jump.
//
// Movements are chosen to serve teaching — follow data, reveal relationships,
// zoom into mechanisms, establish context — not decorative motion.
//
// Example:
//   const shots = sequenceShots([
//     establish('est', board, 0, 0.8, W, H),
//     pushIn('detail', node, 1.0, 1.1, W, H, {intensity: 1.15}),
//     orbit('around', pivot, 20, 340, 0, 2.2, W, H, {radius: 260}),
//     pullBack('context', subject, 4.0, 1.2, W, H),
//     impactShake('hit', {x: 400, y: 260}, 5.6, 0.45, W, H, {from: last}),
//   ], {width: W, height: H});

import type {EasingName} from './types.ts';
import {ease} from './easing.ts';
import {
  identityTransform,
  fitRegion,
  centerPoint,
  lerpTransform,
  type CameraShot,
  type CameraKey,
  type CameraTransform,
  type CameraShotType,
  type Point,
  type Rect,
} from './camera.ts';

export type MoveOptions = {
  from?: CameraTransform; // start transform (composition with the previous shot)
  minScale?: number;
  maxScale?: number;
  easing?: EasingName;
  intensity?: number; // 1 = textbook move; >1 overshoots/extrapolates
};

export type FitMoveOptions = MoveOptions & {margin?: number; minScale?: number; maxScale?: number};

const ID = (w: number, h: number) => identityTransform(w, h);
const iOf = (o?: MoveOptions) => (o?.intensity ?? 1);
const easeOf = (o?: MoveOptions, d = 'easeInOut'): EasingName => o?.easing ?? (d as EasingName);
const lerpPt = (a: Point, b: Point, u: number): Point => ({x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u});

const snap = (v: number) => {
  const rounded = Number(v.toFixed(12));
  return Math.abs(rounded) < 1e-12 ? 0 : rounded;
};

function shot(id: string, op: CameraShotType, start: number, keys: CameraKey[], easing: EasingName, region?: Rect): CameraShot {
  const cleanKeys = keys.map((k) => ({t: snap(k.t), cx: snap(k.cx), cy: snap(k.cy), scale: snap(k.scale)}));
  const first = cleanKeys[0].t;
  const last = cleanKeys[cleanKeys.length - 1].t;
  return {id, op, start: snap(start), duration: snap(Math.max(0.001, last - first)), easing, keys: cleanKeys, region};
}

// move `from` → `to`, scaled by `intensity` (extrapolates past `to` when > 1).
function easedMove(id: string, op: CameraShotType, from: CameraTransform, to: CameraTransform, start: number, duration: number, easing: EasingName, intensity: number, region?: Rect): CameraShot {
  const end = lerpTransform(from, to, intensity);
  return shot(id, op, start, [{t: start, ...from}, {t: start + duration, ...end}], easing, region);
}

const isRect = (p: Point | Rect): p is Rect => typeof (p as Rect).w === 'number';
const toPoint = (p: Point | Rect): Point => (isRect(p) ? centerPoint(p) : (p as Point));

// ---------------------------------------------------------------------------
// Zoom movements
// ---------------------------------------------------------------------------

// Push in from the current view toward a focal region (macro → micro).
export function pushIn(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts: FitMoveOptions = {}): CameraShot {
  const from = opts.from ?? ID(width, height);
  const to = fitRegion(region, width, height, opts.margin ?? 60, opts.minScale, opts.maxScale);
  return easedMove(id, 'pushin', from, to, start, duration, easeOf(opts, 'easeOut'), iOf(opts), region);
}

// High-energy punch-in: a fast, overshooting zoom to a focal region that
// settles on the target at the end. The scene-start / "let me show you this"
// move — same framing as pushIn but with momentum and an impact settle.
export function snapZoom(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts: FitMoveOptions = {}): CameraShot {
  const from = opts.from ?? ID(width, height);
  const to = fitRegion(region, width, height, opts.margin ?? 40, opts.minScale ?? 1.6, opts.maxScale ?? 5);
  const peak = lerpTransform(from, to, Math.max(1.05, iOf(opts) * 1.05));
  return shot(id, 'pushin', start, [{t: start, ...from}, {t: start + duration * 0.72, ...peak}, {t: start + duration, ...to}], 'easeOut', region);
}

// Step out from a tight subject to a wider region (micro → macro context).
export function pullOut(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts: FitMoveOptions = {}): CameraShot {
  const tight = fitRegion(region, width, height, opts.margin ?? 10, opts.minScale, opts.maxScale);
  const from = opts.from ?? tight;
  return easedMove(id, 'pullout', from, ID(width, height), start, duration, easeOf(opts, 'easeInOut'), iOf(opts), region);
}

// Reveal/pull-back: start close on a subject, retreat to the full canvas.
export function pullBack(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts: FitMoveOptions = {}): CameraShot {
  const from = opts.from ?? fitRegion(region, width, height, opts.margin ?? 30, opts.minScale, opts.maxScale);
  return easedMove(id, 'pullback', from, ID(width, height), start, duration, easeOf(opts, 'easeInOut'), iOf(opts), region);
}

// ---------------------------------------------------------------------------
// Lateral movements
// ---------------------------------------------------------------------------

export type SlideOptions = MoveOptions & {axis?: 'x' | 'y'; scale?: number};

// Horizontal / vertical tracking at a constant zoom (explicit axis keeps the
// camera on a clean line, useful for scrolling data structures).
export function slide(id: string, from: Point, to: Point, start: number, duration: number, width: number, height: number, opts: SlideOptions = {}): CameraShot {
  const scale = opts.scale ?? 1.15;
  const base = opts.from ?? {cx: from.x, cy: from.y, scale};
  const a = {cx: base.cx, cy: base.cy, scale: base.scale};
  let b = {cx: to.x, cy: to.y, scale: base.scale};
  if (opts.axis === 'x') b = {...b, cy: base.cy};
  if (opts.axis === 'y') b = {...b, cx: base.cx};
  return easedMove(id, 'slide', a, b, start, duration, easeOf(opts, 'easeInOut'), iOf(opts));
}

// Keep a moving target (a point in canvas space) centred at a fixed zoom.
export function followTarget(id: string, at: (t: number) => Point, start: number, duration: number, width: number, height: number, opts: MoveOptions & {scale?: number; step?: number} = {}): CameraShot {
  const scale = opts.scale ?? 1.4;
  const from = opts.from ?? {cx: at(start).x, cy: at(start).y, scale};
  const step = opts.step ?? Math.max(0.05, duration / 30);
  const keys: CameraKey[] = [{t: start, ...from}];
  const end = start + duration;
  for (let t = start + step; t <= end + 1e-6; t += step) {
    const p = at(Math.min(t, end));
    keys.push({t: Math.min(t, end), cx: p.x, cy: p.y, scale});
  }
  const finalPoint = at(end);
  if (keys.length === 1) keys.push({t: end, cx: finalPoint.x, cy: finalPoint.y, scale});
  else keys[keys.length - 1] = {...keys[keys.length - 1], t: end, cx: finalPoint.x, cy: finalPoint.y, scale};
  return shot(id, 'follow', start, keys, 'linear');
}

export type PanBetweenOptions = MoveOptions & {
  scale?: number;
  // when true, both focal objects stay in view for the whole pass (compare-lite)
  keepBoth?: boolean;
};

// Smooth focal handoff between two objects/points. With keepBoth the camera
// passes through a framing that contains both before settling on the target.
export function panBetween(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts: PanBetweenOptions = {}): CameraShot {
  const pa = toPoint(a);
  const pb = toPoint(b);
  const scale = opts.scale ?? 1.25;
  const from = opts.from ?? {cx: pa.x, cy: pa.y, scale};
  if (!opts.keepBoth) {
    return easedMove(id, 'pan', from, {cx: pb.x, cy: pb.y, scale}, start, duration, easeOf(opts, 'easeInOut'), iOf(opts));
  }
  const both = 'w' in a && 'w' in b ? unionOf(a as Rect, b as Rect) : null;
  const via = both ? fitRegion(both, width, height, 60, opts.minScale, opts.maxScale) : {cx: (pa.x + pb.x) / 2, cy: (pa.y + pb.y) / 2, scale};
  const keys: CameraKey[] = [
    {t: start, ...from},
    {t: start + duration / 2, cx: via.cx, cy: via.cy, scale: via.scale},
    {t: start + duration, cx: pb.x, cy: pb.y, scale},
  ];
  return shot(id, 'handoff', start, keys, easeOf(opts, 'easeInOut'));
}

// Explicit focus-handoff primitive: passes the viewer from object/point `a` to
// `b` while keeping both in frame mid-pass. Sugar over panBetween({keepBoth}).
export function handoffFocus(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts: PanBetweenOptions = {}): CameraShot {
  return panBetween(id, a, b, start, duration, width, height, {...opts, keepBoth: true});
}

function unionOf(a: Rect, b: Rect): Rect {
  const x0 = Math.min(a.x, b.x);
  const y0 = Math.min(a.y, b.y);
  const x1 = Math.max(a.x + a.w, b.x + b.w);
  const y1 = Math.max(a.y + a.h, b.y + b.h);
  return {x: x0, y: y0, w: x1 - x0, h: y1 - y0};
}

// ---------------------------------------------------------------------------
// Arc / orbit
// ---------------------------------------------------------------------------

export type OrbitOptions = MoveOptions & {radius?: number; sagitta?: number; scale?: number};

// Arc (curved dolly) between two focal points. `sagitta` (px, screen-normalized
// via scale) pushes the path out perpendicular to the direct line so the move
// reads as a swing around the objects instead of a straight push.
export function arcPan(id: string, a: Point, b: Point, start: number, duration: number, width: number, height: number, opts: OrbitOptions = {}): CameraShot {
  const scale = opts.scale ?? 1.2;
  const from = opts.from ?? {cx: a.x, cy: a.y, scale};
  const p0 = {x: from.cx, y: from.cy};
  const p1 = {x: b.x, y: b.y};
  const mid = lerpPt(p0, p1, 0.5);
  const sag = ((opts.sagitta ?? 90) * iOf(opts)) / scale + 1e-9; // screen px -> canvas units
  const dx = p1.x - p0.x;
  const dy = p1.y - p0.y;
  const len = Math.hypot(dx, dy) || 1;
  const bend: Point = {x: mid.x + (-dy / len) * sag, y: mid.y + (dx / len) * sag};
  const n = Math.max(8, Math.round(duration / 0.08));
  const keys: CameraKey[] = [];
  for (let i = 0; i <= n; i += 1) {
    const u = i === Math.round(n / 2) ? 0.5 : i / n;
    const inv = 1 - u;
    const c = {
      x: inv * inv * p0.x + 2 * inv * u * bend.x + u * u * p1.x,
      y: inv * inv * p0.y + 2 * inv * u * bend.y + u * u * p1.y,
    };
    keys.push({t: start + u * duration, cx: c.x, cy: c.y, scale});
  }
  return shot(id, 'orbit', start, keys, 'linear');
}

// Swing the camera around a pivot. `startDeg`..`endDeg` (degrees clockwise,
// y-down screen space) trace an arc of radius `radius` (canvas units) around
// the pivot while holding zoom. Sweep endDeg - startDeg across the duration.
export function orbit(id: string, pivot: Point, startDeg: number, endDeg: number, start: number, duration: number, width: number, height: number, opts: OrbitOptions = {}): CameraShot {
  const scale = opts.scale ?? 1.15;
  const radius = (opts.radius ?? Math.min(width, height) * 0.45) * iOf(opts);
  const n = Math.max(16, Math.round(duration / 0.07));
  const keys: CameraKey[] = [];
  for (let i = 0; i <= n; i += 1) {
    const u = i / n;
    const rad = ((startDeg + (endDeg - startDeg) * u) * Math.PI) / 180;
    keys.push({
      t: start + u * duration,
      cx: pivot.x + Math.cos(rad) * radius,
      cy: pivot.y + Math.sin(rad) * radius,
      scale,
    });
  }
  return shot(id, 'orbit', start, keys, 'linear');
}

// ---------------------------------------------------------------------------
// Push/zoom hybrids & rhythm
// ---------------------------------------------------------------------------

export type DollyOptions = MoveOptions & {toScale?: number; anchor?: Point};

// Dolly + zoom: the focal canvas point stays glued to a fixed screen `anchor`
// while the zoom changes, so surrounding context streams past it (vertigo
// effect when anchor is off-centre). Default anchor is screen centre → a
// straight zoom on the focal point.
export function dollyZoom(id: string, focal: Point, start: number, duration: number, width: number, height: number, opts: DollyOptions = {}): CameraShot {
  const from = opts.from ?? ID(width, height);
  const s0 = from.scale;
  const s1 = opts.toScale ?? s0 * 1.8;
  const intensity = iOf(opts);
  const sEnd = s0 + (s1 - s0) * intensity;
  const anchor = opts.anchor ?? {x: width / 2, y: height / 2};
  const easing = easeOf(opts, 'easeInOut');
  const centerAt = (s: number) => ({cx: focal.x - (anchor.x - width / 2) / s, cy: focal.y - (anchor.y - height / 2) / s, scale: s});
  const n = Math.max(16, Math.round(duration / 0.06));
  const keys: CameraKey[] = [];
  for (let i = 0; i <= n; i += 1) {
    const u = i / n;
    const s = s0 + (sEnd - s0) * ease(u, easing);
    keys.push({t: start + u * duration, ...centerAt(s)});
  }
  return shot(id, 'dolly', start, keys, 'linear');
}

// Macro → micro → macro: dive into a mechanism, then resurface to the whole.
export function macroMicroMacro(id: string, micro: Rect, start: number, duration: number, width: number, height: number, opts: FitMoveOptions = {}): CameraShot {
  const base = opts.from ?? ID(width, height);
  const to = fitRegion(micro, width, height, opts.margin ?? 30, opts.minScale, opts.maxScale);
  const peak = lerpTransform(base, to, Math.max(0, Math.min(1, iOf(opts))));
  const half = start + duration / 2;
  return shot(id, 'macro', start, [{t: start, ...base}, {t: half, ...peak}, {t: start + duration, ...base}], easeOf(opts, 'easeInOut'), micro);
}

// ---------------------------------------------------------------------------
// Impact & energy
// ---------------------------------------------------------------------------

export type ShakeOptions = MoveOptions & {amplitude?: number; shakes?: number};

// Controlled impact shake around a resting transform. `amplitude` is peak
// screen-space drift in px; offsets decay to zero by the end (the camera
// returns exactly to rest, so it never leaves a shot misaligned).
export function impactShake(id: string, at: CameraTransform, start: number, duration: number, width: number, height: number, opts: ShakeOptions = {}): CameraShot {
  const ampScreen = opts.amplitude ?? 14;
  const shakes = opts.shakes ?? Math.max(1, Math.round(duration / 0.12));
  const base = opts.from ?? at;
  const n = Math.max(12, Math.round(duration / 0.03));
  const scale = base.scale || 1;
  const keys: CameraKey[] = [];
  for (let i = 0; i <= n; i += 1) {
    const u = i / n;
    const decay = (1 - u) * (1 - u);
    const wave = Math.sin(u * shakes * Math.PI * 2);
    const wave2 = Math.sin(u * shakes * Math.PI * 2 + 1.3);
    keys.push({
      t: start + u * duration,
      cx: base.cx + (wave * ampScreen * decay) / scale,
      cy: base.cy + (wave2 * ampScreen * 0.7 * decay) / scale,
      scale,
    });
  }
  keys[0] = {t: start, ...base};
  keys[keys.length - 1] = {t: start + duration, ...base};
  return shot(id, 'shake', start, keys, 'linear');
}

export type WhipOptions = PanBetweenOptions & {overshoot?: number};

// Directional/whip transition: a fast, momentum-heavy pan to the next focal
// point (easeOut with overshoot reads as follow-through past the target).
export function whipPan(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts: WhipOptions = {}): CameraShot {
  const pa = toPoint(a);
  const pb = toPoint(b);
  const scale = opts.scale ?? 1.3;
  const from = opts.from ?? {cx: pa.x, cy: pa.y, scale};
  const over = opts.overshoot ?? 0.12;
  const dx = pb.x - from.cx;
  const dy = pb.y - from.cy;
  const keys: CameraKey[] = [
    {t: start, ...from},
    {t: start + duration * 0.55, cx: from.cx + dx * (1 + over), cy: from.cy + dy * (1 + over), scale},
    {t: start + duration, cx: pb.x, cy: pb.y, scale},
  ];
  return shot(id, 'whip', start, keys, 'easeInOut');
}

// ---------------------------------------------------------------------------
// Atmosphere
// ---------------------------------------------------------------------------

export type DriftOptions = MoveOptions & {amplitude?: number; period?: number; breathing?: boolean};

// Parallax-style drift: a subtle, looping background slide (returns near its
// origin). `amplitude` is screen-space drift in px. Useful to keep an otherwise
// static establish shot gently alive without drawing attention.
export function parallaxDrift(id: string, start: number, duration: number, width: number, height: number, opts: DriftOptions = {}): CameraShot {
  const base = opts.from ?? ID(width, height);
  const ampPx = opts.amplitude ?? Math.min(width, height) * 0.008;
  const period = opts.period ?? Math.max(duration, 2.4);
  const scale = base.scale;
  const amp = ampPx / scale;
  const n = Math.max(24, Math.round(duration / 0.08));
  const evenN = n % 2 === 1 ? n + 1 : n;
  const keys: CameraKey[] = [];
  for (let i = 0; i <= evenN; i += 1) {
    const u = i / evenN;
    const ph = u * Math.PI * 2;
    const driftWave = Math.sin(ph - Math.PI / 2);
    const yWave = Math.sin(ph * 0.83 + Math.PI / 3);
    const breath = opts.breathing ? Math.sin(ph * 0.5 + Math.PI / 2) * 0.02 : 0;
    keys.push({
      t: start + u * duration,
      cx: base.cx + driftWave * amp,
      cy: base.cy + yWave * amp * 0.8,
      scale: scale * (1 + breath),
    });
  }
  keys[0] = {t: start, ...base};
  keys[keys.length - 1] = {t: start + duration, ...base};
  return shot(id, 'drift', start, keys, 'linear');
}

// ---------------------------------------------------------------------------
// Composition / continuity
// ---------------------------------------------------------------------------

// Lay a list of shots end-to-end with NO jumps: each shot starts exactly when
// the previous one ends and inherits the previous shot's final transform as its
// opening keyframe. Shots that authored their own opening (e.g. establish)
// keep it for the first element.
export function sequenceShots(shots: readonly CameraShot[]): CameraShot[] {
  const out: CameraShot[] = [];
  let cursor = shots.length > 0 ? shots[0].start : 0;
  let prevEnd: CameraTransform | null = null;
  for (let i = 0; i < shots.length; i += 1) {
    const src = shots[i];
    const originalStart = src.start;
    const start = i === 0 ? originalStart : cursor;
    const keys: CameraKey[] = [];
    if (i === 0) {
      for (const k of src.keys) keys.push({t: k.t, cx: k.cx, cy: k.cy, scale: k.scale});
    } else {
      keys.push({t: start, cx: prevEnd!.cx, cy: prevEnd!.cy, scale: prevEnd!.scale});
      const offset = start - originalStart;
      for (const k of src.keys) {
        if (k.t <= originalStart + 1e-6) continue;
        keys.push({t: k.t + offset, cx: k.cx, cy: k.cy, scale: k.scale});
      }
    }
    out.push({...src, start, duration: src.duration, keys});
    cursor = start + src.duration;
    const last = keys[keys.length - 1];
    prevEnd = {cx: last.cx, cy: last.cy, scale: last.scale};
  }
  return out;
}
