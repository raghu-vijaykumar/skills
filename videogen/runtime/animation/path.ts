// Reusable, geometry-derived paths. A Path is a pure function from a
// parameter u in [0,1] to points along the trajectory, plus helpers for
// sampling, length and bounds so validators can reason about the full path.

export type Point = {x: number; y: number};
export type Rect = {x: number; y: number; w: number; h: number};
export type PathKind = 'linear' | 'arc' | 'bezier' | 'orthogonal' | 'curved' | 'follow-link';

export type PathOptions = {
  // arc: how far the midpoint bows from the chord (0 = straight).
  sagitta?: number;
  // bezier/curved: optional explicit control points (two for bezier).
  control?: Point[];
  // orthogonal: which axis bends first.
  firstAxis?: 'x' | 'y';
  // follow-link: polyline through waypoints (a, waypoints, b).
  waypoints?: Point[];
  // sampling resolution used by length/bounds helpers.
  segments?: number;
};

export type Path = {
  kind: PathKind;
  a: Point;
  b: Point;
  pointAt: (u: number) => Point;
  samples: (n?: number) => Point[];
  length: () => number;
  bounds: () => Rect;
  offsetPoint: (u: number, normalOffset: number) => Point;
};

const clamp = (v: number) => Math.max(0, Math.min(1, v));

export function buildPath(kind: PathKind, a: Point, b: Point, options: PathOptions = {}): Path {
  switch (kind) {
    case 'linear':
      return linear(a, b);
    case 'orthogonal':
      return orthogonal(a, b, options);
    case 'arc':
      return arc(a, b, options);
    case 'bezier':
      return bezier(a, b, options);
    case 'curved':
      return curved(a, b, options);
    case 'follow-link':
      return followLink(a, b, options);
    default:
      return linear(a, b);
  }
}

function linear(a: Point, b: Point): Path {
  return makePath('linear', a, b, (u) => ({x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u}));
}

function orthogonal(a: Point, b: Point, options: PathOptions): Path {
  const firstX = (options.firstAxis ?? 'x') === 'x';
  const corner = firstX ? {x: b.x, y: a.y} : {x: a.x, y: b.y};
  const leg1 = linear(a, corner);
  const leg2 = linear(corner, b);
  const len1 = leg1.length();
  const len2 = leg2.length();
  if (len1 <= 1e-9 && len2 <= 1e-9) return linear(a, b);
  if (len1 <= 1e-9) return leg2;
  if (len2 <= 1e-9) return leg1;
  const total = len1 + len2;
  return makePath('orthogonal', a, b, (u) => {
    const d = u * total;
    return d <= len1 + 1e-9 ? leg1.pointAt(Math.min(1, d / len1)) : leg2.pointAt(Math.min(1, (d - len1) / len2));
  });
}

function arc(a: Point, b: Point, options: PathOptions): Path {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const sag = options.sagitta ?? Math.max(40, len * 0.18);
  const cx = mx + nx * sag;
  const cy = my + ny * sag;
  return bezier(a, b, {control: [{x: cx, y: cy}, {x: cx, y: cy}], segments: options.segments});
}

function bezier(a: Point, b: Point, options: PathOptions): Path {
  const c1 = options.control?.[0] ?? mid(a, b, 0.3);
  const c2 = options.control?.[1] ?? mid(a, b, 0.7);
  return makePath('bezier', a, b, (u) => {
    const v = 1 - u;
    return {
      x: v * v * v * a.x + 3 * v * v * u * c1.x + 3 * v * u * u * c2.x + u * u * u * b.x,
      y: v * v * v * a.y + 3 * v * v * u * c1.y + 3 * v * u * u * c2.y + u * u * u * b.y,
    };
  });
}

function curved(a: Point, b: Point, options: PathOptions): Path {
  // A gentle single control bulging perpendicular to the chord (S-curve feel).
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const mx = (a.x + b.x) / 2 + nx * (len * 0.18);
  const my = (a.y + b.y) / 2 + ny * (len * 0.18);
  return bezier(a, b, {control: [{x: mx, y: my}, {x: mx, y: my}], segments: options.segments});
}

function followLink(a: Point, b: Point, options: PathOptions): Path {
  const pts = [a, ...(options.waypoints ?? []), b];
  const legs: Path[] = [];
  let total = 0;
  for (let i = 0; i < pts.length - 1; i += 1) {
    const leg = linear(pts[i], pts[i + 1]);
    legs.push(leg);
    total += leg.length();
  }
  const n = legs.length;
  const breakpoints: number[] = [];
  let acc = 0;
  for (let i = 0; i < n; i += 1) {
    acc += legs[i].length();
    if (acc > 1e-9 && total > 1e-9) breakpoints.push(acc / total);
  }

  const base = makePath('follow-link', a, b, (u) => {
    const d = clamp(u) * total;
    let acc = 0;
    for (let i = 0; i < n; i += 1) {
      const leg = legs[i];
      if (acc + leg.length() >= d) {
        const local = leg.length() > 0 ? (d - acc) / leg.length() : 0;
        return leg.pointAt(Math.min(1, Math.max(0, local)));
      }
      acc += leg.length();
    }
    return pts[pts.length - 1];
  });

  const samples = (sampleCount: number = 64) => {
    const points: Point[] = [];
    const seen = new Set<string>();
    const add = (p: Point) => {
      const key = `${p.x.toFixed(6)}:${p.y.toFixed(6)}`;
      if (!seen.has(key)) {
        seen.add(key);
        points.push(p);
      }
    };
    for (let i = 0; i <= sampleCount; i += 1) add(base.pointAt(i / sampleCount));
    for (const u of breakpoints) add(base.pointAt(u));
    return points;
  };

  return {
    ...base,
    length: () => total,
    bounds: () => {
      const pts = samples();
      const xs = pts.map((p) => p.x);
      const ys = pts.map((p) => p.y);
      return {x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys)};
    },
    samples,
  };
}

function mid(a: Point, b: Point, u: number): Point {
  return {x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u};
}

function makePath(kind: PathKind, a: Point, b: Point, pointAt: (u: number) => Point): Path {
  const SAMPLES = 64;
  let cachedLength: number | null = null;
  let cachedBounds: Rect | null = null;
  const samples = (n: number = SAMPLES) => {
    const pts: Point[] = [];
    for (let i = 0; i <= n; i += 1) pts.push(pointAt(i / n));
    return pts;
  };
  const length = () => {
    if (cachedLength != null) return cachedLength;
    const pts = samples();
    let total = 0;
    for (let i = 0; i < pts.length - 1; i += 1) total += Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y);
    cachedLength = total;
    return total;
  };
  const bounds = () => {
    if (cachedBounds) return cachedBounds;
    const pts = samples();
    const xs = pts.map((p) => p.x);
    const ys = pts.map((p) => p.y);
    const x0 = Math.min(...xs);
    const x1 = Math.max(...xs);
    const y0 = Math.min(...ys);
    const y1 = Math.max(...ys);
    cachedBounds = {x: x0, y: y0, w: x1 - x0, h: y1 - y0};
    return cachedBounds;
  };
  const offsetPoint = (u: number, offset: number) => {
    const p = pointAt(clamp(u));
    const q = pointAt(clamp(Math.min(1, u + 0.01)));
    const dx = q.x - p.x;
    const dy = q.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    return {x: p.x + (-dy / len) * offset, y: p.y + (dx / len) * offset};
  };
  return {kind, a, b, pointAt, samples, length, bounds, offsetPoint};
}
