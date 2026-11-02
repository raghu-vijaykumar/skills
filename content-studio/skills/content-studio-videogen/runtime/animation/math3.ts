// Deterministic mathematical 2.5D projection — the reusable core for the 2.5D
// mathematical-animation milestone (docs/2.5d-animation-roadmap.md).
//
// A `MathCamera` orbits a point in a math world (x, y, z) and projects world
// points to screen space with real perspective and depth, so a surface
// z = f(x, y) — with its grid, axes, gradient vectors and contour lines — can be
// drawn in the existing 2D renderer as a genuine 3D structure projected to 2D
// ("2.5D"). This is deliberately NOT a general 3D scene framework: there are no
// meshes, lights or materials here, only the math needed to stage and project
// the geometry. Shading/color stay a render-time concern (design tokens).
//
// Pure and Node-safe: no DOM, no randomness, no wall-clock. Every function is a
// deterministic function of its inputs, so scenes and validators share one
// source of truth for where a mathematical object sits on screen.

export type Vec3 = {x: number; y: number; z: number};

// Orbit camera. `target` is the world point looked at; `distance` the camera's
// distance from it; `yaw` the azimuth (radians, around the vertical z axis);
// `pitch` the elevation (radians, above the xy plane); `fov` the vertical field
// of view (radians). Larger `fov` = wider/stronger perspective.
export type MathCamera = {
  target: Vec3;
  distance: number;
  yaw: number;
  pitch: number;
  fov: number;
};

export const MATH_CAMERA_DEFAULTS: Pick<MathCamera, 'distance' | 'yaw' | 'pitch' | 'fov'> = {
  distance: 8,
  yaw: -0.6,
  pitch: 0.85,
  fov: (52 * Math.PI) / 180,
};

export type ScreenPoint = {x: number; y: number; depth: number; scale: number};

export type Segment = {a: Vec3; b: Vec3};

// ---- vector algebra ---------------------------------------------------------

export const v3 = (x: number, y: number, z: number): Vec3 => ({x, y, z});
export const add3 = (a: Vec3, b: Vec3): Vec3 => ({x: a.x + b.x, y: a.y + b.y, z: a.z + b.z});
export const sub3 = (a: Vec3, b: Vec3): Vec3 => ({x: a.x - b.x, y: a.y - b.y, z: a.z - b.z});
export const scale3 = (a: Vec3, s: number): Vec3 => ({x: a.x * s, y: a.y * s, z: a.z * s});
export const dot3 = (a: Vec3, b: Vec3): number => a.x * b.x + a.y * b.y + a.z * b.z;
export const cross3 = (a: Vec3, b: Vec3): Vec3 => ({
  x: a.y * b.z - a.z * b.y,
  y: a.z * b.x - a.x * b.z,
  z: a.x * b.y - a.y * b.x,
});
export const len3 = (a: Vec3): number => Math.hypot(a.x, a.y, a.z);
export const norm3 = (a: Vec3): Vec3 => {
  const l = len3(a);
  return l < 1e-12 ? v3(0, 0, 0) : scale3(a, 1 / l);
};

// ---- camera -----------------------------------------------------------------

export function mathCamera(target: Vec3, partial: Partial<MathCamera> = {}): MathCamera {
  return {...MATH_CAMERA_DEFAULTS, target, ...partial};
}

export type CameraBasis = {pos: Vec3; right: Vec3; up: Vec3; forward: Vec3};

// World-up is +z. A look-at basis where `forward` points from the camera toward
// the target, `right` is screen-right and `up` is screen-up.
export function cameraBasis(cam: MathCamera): CameraBasis {
  const cp = Math.cos(cam.pitch);
  const pos = v3(
    cam.target.x + cam.distance * cp * Math.cos(cam.yaw),
    cam.target.y + cam.distance * cp * Math.sin(cam.yaw),
    cam.target.z + cam.distance * Math.sin(cam.pitch),
  );
  const forward = norm3(sub3(cam.target, pos));
  const worldUp = v3(0, 0, 1);
  let right = cross3(forward, worldUp);
  if (len3(right) < 1e-9) right = v3(1, 0, 0);
  right = norm3(right);
  const up = cross3(right, forward);
  return {pos, right, up, forward};
}

export function focalLength(cam: MathCamera, height: number): number {
  return height / 2 / Math.tan(cam.fov / 2);
}

// ---- camera animation -------------------------------------------------------

export type MathCameraKey = {t: number; cam: MathCamera};

// Interpolate two orbit cameras. Angles interpolate directly (a straight yaw /
// pitch sweep), which is how orbit controls move; no shortest-arc handling.
export function lerpMathCamera(a: MathCamera, b: MathCamera, u: number): MathCamera {
  const c = Math.max(0, Math.min(1, u));
  return {
    target: {
      x: a.target.x + (b.target.x - a.target.x) * c,
      y: a.target.y + (b.target.y - a.target.y) * c,
      z: a.target.z + (b.target.z - a.target.z) * c,
    },
    distance: a.distance + (b.distance - a.distance) * c,
    yaw: a.yaw + (b.yaw - a.yaw) * c,
    pitch: a.pitch + (b.pitch - a.pitch) * c,
    fov: a.fov + (b.fov - a.fov) * c,
  };
}

// Resolve a keyframed math camera at time `now` (piecewise linear, held at the
// ends). Mirrors `cameraTransformAt` for the 2D camera: deterministic and
// Node-safe, so a scene and a validator sample the same orbit.
export function mathCameraAt(now: number, keys: readonly MathCameraKey[]): MathCamera {
  if (keys.length === 0) return mathCamera(v3(0, 0, 0));
  if (now <= keys[0].t) return keys[0].cam;
  const last = keys[keys.length - 1];
  if (now >= last.t) return last.cam;
  let i = 0;
  while (i < keys.length - 2 && keys[i + 1].t <= now) i += 1;
  const a = keys[i];
  const b = keys[i + 1];
  const u = (now - a.t) / Math.max(1e-6, b.t - a.t);
  return lerpMathCamera(a.cam, b.cam, u);
}

// Project a world point to screen space. `depth` is the distance along the view
// axis (positive in front of the camera, larger = farther); `scale` is the
// perspective scale at that depth (analogous to the flat camera's scale).
export function projectPoint(cam: MathCamera, p: Vec3, width: number, height: number): ScreenPoint {
  const {pos, right, up, forward} = cameraBasis(cam);
  const rel = sub3(p, pos);
  const depth = dot3(rel, forward);
  const scale = focalLength(cam, height) / Math.max(depth, NEAR_PLANE);
  return {
    x: width / 2 + dot3(rel, right) * scale,
    y: height / 2 - dot3(rel, up) * scale,
    depth,
    scale,
  };
}

// Minimum depth a projected point may have before it must be clipped. Points at
// or behind this plane would otherwise project to enormous/inverted coordinates.
export const NEAR_PLANE = 1e-3;

// True when a world point is at or behind the camera's near plane and must be
// clipped before rendering (its `projectPoint` depth is <= NEAR_PLANE).
export function isBehindCamera(cam: MathCamera, p: Vec3): boolean {
  const {pos, forward} = cameraBasis(cam);
  return dot3(sub3(p, pos), forward) <= NEAR_PLANE;
}

export function projectSegment(cam: MathCamera, seg: Segment, width: number, height: number): {a: ScreenPoint; b: ScreenPoint} {
  return {a: projectPoint(cam, seg.a, width, height), b: projectPoint(cam, seg.b, width, height)};
}

export function projectPolyline(cam: MathCamera, pts: readonly Vec3[], width: number, height: number): ScreenPoint[] {
  return pts.map((p) => projectPoint(cam, p, width, height));
}

// ---- scalar fields / surfaces ----------------------------------------------

export type SurfaceGrid = {
  nx: number;
  ny: number;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
  z: number[][]; // z[j][i], j = y index, i = x index
};

export function sampleSurface(f: (x: number, y: number) => number, x0: number, x1: number, y0: number, y1: number, nx: number, ny: number): SurfaceGrid {
  const nxSafe = Math.max(1, Math.floor(nx));
  const nySafe = Math.max(1, Math.floor(ny));
  const z: number[][] = [];
  for (let j = 0; j <= nySafe; j += 1) {
    const row: number[] = [];
    const y = y0 + (j / nySafe) * (y1 - y0);
    for (let i = 0; i <= nxSafe; i += 1) {
      const x = x0 + (i / nxSafe) * (x1 - x0);
      row.push(f(x, y));
    }
    z.push(row);
  }
  return {nx: nxSafe, ny: nySafe, x0, x1, y0, y1, z};
}

export function gridX(grid: SurfaceGrid, i: number): number {
  return grid.x0 + (i / grid.nx) * (grid.x1 - grid.x0);
}

export function gridY(grid: SurfaceGrid, j: number): number {
  return grid.y0 + (j / grid.ny) * (grid.y1 - grid.y0);
}

export type SurfaceQuad = {
  i: number;
  j: number;
  corners: [Vec3, Vec3, Vec3, Vec3];
  center: Vec3;
  normal: Vec3; // unit normal facing up (z > 0)
};

// The surface as axis-aligned quads in the xy plane (CCW seen from above) with
// per-quad face normals for shading. Painter's-algorithm sorting is done at
// render time from the projected depths.
export function surfaceQuads(grid: SurfaceGrid): SurfaceQuad[] {
  const quads: SurfaceQuad[] = [];
  for (let j = 0; j < grid.ny; j += 1) {
    for (let i = 0; i < grid.nx; i += 1) {
      const a = v3(gridX(grid, i), gridY(grid, j), grid.z[j][i]);
      const b = v3(gridX(grid, i + 1), gridY(grid, j), grid.z[j][i + 1]);
      const c = v3(gridX(grid, i + 1), gridY(grid, j + 1), grid.z[j + 1][i + 1]);
      const d = v3(gridX(grid, i), gridY(grid, j + 1), grid.z[j + 1][i]);
      const center = v3((a.x + c.x) / 2, (a.y + c.y) / 2, (a.z + b.z + c.z + d.z) / 4);
      quads.push({i, j, corners: [a, b, c, d], center, normal: quadNormal(a, b, c)});
    }
  }
  return quads;
}

function quadNormal(a: Vec3, b: Vec3, c: Vec3): Vec3 {
  const n = cross3(sub3(b, a), sub3(c, a));
  const l = len3(n);
  if (l < 1e-12) return v3(0, 0, 1);
  const unit = scale3(n, 1 / l);
  return unit.z < 0 ? scale3(unit, -1) : unit;
}

// Lambert diffuse shading factor in [0, 1] from a unit surface normal and a
// light direction. `light` is normalized internally.
export function lambert(normal: Vec3, light: Vec3): number {
  return Math.max(0, dot3(normal, norm3(light)));
}

// ---- gradients --------------------------------------------------------------

// Numerical gradient of a scalar field f(x, y) (central differences).
export function gradient2(f: (x: number, y: number) => number, x: number, y: number, h = 1e-3): {dx: number; dy: number} {
  return {
    dx: (f(x + h, y) - f(x - h, y)) / (2 * h),
    dy: (f(x, y + h) - f(x, y - h)) / (2 * h),
  };
}

// The steepest-ascent direction in the tangent plane at (x, y, f(x, y)): the
// 3D vector (gx, gy, gx² + gy²) — a step (gx, gy) in the xy plane lifts the
// surface by exactly gx² + gy².
export function steepestTangent(f: (x: number, y: number) => number, x: number, y: number, h = 1e-3): Vec3 {
  const g = gradient2(f, x, y, h);
  return v3(g.dx, g.dy, g.dx * g.dx + g.dy * g.dy);
}

// ---- contours ---------------------------------------------------------------

const lerp = (a: number, b: number, u: number) => a + (b - a) * u;

// Marching-squares level curves of the sampled field at `level`. Returns raw
// segments on the surface; stitch them with `chainSegments` for polylines.
export function contourSegments(grid: SurfaceGrid, level: number): Segment[] {
  const segs: Segment[] = [];
  const value = (i: number, j: number) => grid.z[j][i] - level;
  const point = (i: number, j: number) => v3(gridX(grid, i), gridY(grid, j), grid.z[j][i]);
  const edgePoint = (i0: number, j0: number, i1: number, j1: number): Vec3 => {
    const v0 = value(i0, j0);
    const v1 = value(i1, j1);
    const u = v0 / (v0 - v1); // value(i0) - u * (value(i0) - value(i1)) == 0
    const p0 = point(i0, j0);
    const p1 = point(i1, j1);
    return v3(lerp(p0.x, p1.x, u), lerp(p0.y, p1.y, u), lerp(p0.z, p1.z, u));
  };
  for (let j = 0; j < grid.ny; j += 1) {
    for (let i = 0; i < grid.nx; i += 1) {
      // corners: (i,j) (i+1,j) (i+1,j+1) (i,j+1)
      const s = [value(i, j), value(i + 1, j), value(i + 1, j + 1), value(i, j + 1)];
      const crossings: Vec3[] = [];
      const edges: Array<[number, number, number, number]> = [
        [i, j, i + 1, j],
        [i + 1, j, i + 1, j + 1],
        [i + 1, j + 1, i, j + 1],
        [i, j + 1, i, j],
      ];
      for (let e = 0; e < 4; e += 1) {
        if (s[e] >= 0 !== s[(e + 1) % 4] >= 0) {
          const [i0, j0, i1, j1] = edges[e];
          crossings.push(edgePoint(i0, j0, i1, j1));
        }
      }
      if (crossings.length === 2) segs.push({a: crossings[0], b: crossings[1]});
      else if (crossings.length === 4) {
        segs.push({a: crossings[0], b: crossings[1]});
        segs.push({a: crossings[2], b: crossings[3]});
      }
    }
  }
  return segs;
}

// Chain contour segments into connected polylines (greedy, deterministic).
export function chainSegments(segs: readonly Segment[], eps = 1e-6): Vec3[][] {
  const remaining = segs.map((s) => ({a: {...s.a}, b: {...s.b}}));
  const out: Vec3[][] = [];
  const eq = (p: Vec3, q: Vec3) => Math.hypot(p.x - q.x, p.y - q.y, p.z - q.z) <= eps;
  while (remaining.length > 0) {
    const start = remaining.pop()!;
    const chain: Vec3[] = [start.a, start.b];
    let grew = true;
    while (grew) {
      grew = false;
      for (let k = remaining.length - 1; k >= 0; k -= 1) {
        const seg = remaining[k];
        if (eq(chain[chain.length - 1], seg.a)) {
          chain.push(seg.b);
          remaining.splice(k, 1);
          grew = true;
        } else if (eq(chain[chain.length - 1], seg.b)) {
          chain.push(seg.a);
          remaining.splice(k, 1);
          grew = true;
        } else if (eq(chain[0], seg.b)) {
          chain.unshift(seg.a);
          remaining.splice(k, 1);
          grew = true;
        } else if (eq(chain[0], seg.a)) {
          chain.unshift(seg.b);
          remaining.splice(k, 1);
          grew = true;
        }
      }
    }
    out.push(chain);
  }
  return out;
}

// ---- domain grid & axes -----------------------------------------------------

// Level curves are one view; the domain grid is the other. Returns polylines in
// the z-plane: vertical lines (constant x) then horizontal lines (constant y).
export function planeGrid(x0: number, x1: number, y0: number, y1: number, nx: number, ny: number, z = 0): Vec3[][] {
  const lines: Vec3[][] = [];
  for (let i = 0; i <= nx; i += 1) {
    const x = x0 + (i / nx) * (x1 - x0);
    const line: Vec3[] = [];
    for (let j = 0; j <= ny; j += 1) line.push(v3(x, y0 + (j / ny) * (y1 - y0), z));
    lines.push(line);
  }
  for (let j = 0; j <= ny; j += 1) {
    const y = y0 + (j / ny) * (y1 - y0);
    const line: Vec3[] = [];
    for (let i = 0; i <= nx; i += 1) line.push(v3(x0 + (i / nx) * (x1 - x0), y, z));
    lines.push(line);
  }
  return lines;
}

// The three coordinate axes as world segments from `origin` of length `length`.
export function axes(origin: Vec3, length: number): {x: Segment; y: Segment; z: Segment} {
  return {
    x: {a: origin, b: add3(origin, v3(length, 0, 0))},
    y: {a: origin, b: add3(origin, v3(0, length, 0))},
    z: {a: origin, b: add3(origin, v3(0, 0, length))},
  };
}

// Arrow head for a 3D segment: the two world segments forming the tip, drawn
// back from `tip` toward `tail` (`size` = head length, `angle` = opening
// half-angle). The two prongs are symmetric across the arrow axis, so the head
// reads as a clean chevron in any orientation.
export function arrowHead(tail: Vec3, tip: Vec3, size: number, angle = Math.PI / 7): [Segment, Segment] {
  const dir = norm3(sub3(tip, tail));
  // A stable reference axis: world +z unless the arrow is nearly vertical, in
  // which case world +x. Cross(dir, ref) is a perpendicular that never vanishes.
  const ref = Math.abs(dir.z) < 0.99 ? v3(0, 0, 1) : v3(1, 0, 0);
  const side = norm3(cross3(dir, ref));
  const base = add3(tip, scale3(dir, -size));
  const offset = scale3(side, size * Math.tan(angle));
  return [
    {a: tip, b: add3(base, offset)},
    {a: tip, b: sub3(base, offset)},
  ];
}
