// Shared deterministic 3D realism utilities for Revise Labs R3F/Three.js videos.
//
// Design contract (matches DESIGN.md):
// - dark cinematic background + LIGHT readable objects, restrained accents
// - everything deterministic from (frame/time, declared inputs): seeded hashes
//   only, no Math.random, no wall-clock, no browser-only state at module scope
// - dependency-free: plain three.js + canvas textures, no new render pipeline
// - cheap by default: fake contact shadows, additive glow sprites, fog for
//   depth. Real shadow maps / optical DOF are intentionally NOT used.
//
// Node-safety: this module must stay import-safe under Node (gates execute
// pure timeline/layout modules directly). All `document` access is lazy inside
// functions called from browser-rendered components only.

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Deterministic noise (seeded hashes only)
// ---------------------------------------------------------------------------

/** Deterministic pseudo-random in [0, 1) from an integer + seed. */
export function hash01(n: number, seed = 1): number {
  const s = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453;
  return s - Math.floor(s);
}

/** Deterministic PRNG (mulberry32). Create per call-site with a fixed seed. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Smooth 1D value noise in [0, 1]. */
export function valueNoise1(x: number, seed = 1): number {
  const i = Math.floor(x);
  const f = x - i;
  const a = hash01(i, seed);
  const b = hash01(i + 1, seed);
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}

/** Fractal 1D noise in [0, 1]. */
export function fbm1(x: number, seed = 1, octaves = 4): number {
  let v = 0;
  let amp = 0.5;
  let f = 1;
  let norm = 0;
  for (let k = 0; k < octaves; k += 1) {
    v += amp * valueNoise1(x * f, seed + k * 17);
    norm += amp;
    amp *= 0.5;
    f *= 2.03;
  }
  return v / Math.max(1e-6, norm);
}

export const clamp01 = (u: number): number => Math.max(0, Math.min(1, u));
export const lerp = (a: number, b: number, u: number): number => a + (b - a) * u;

// ---------------------------------------------------------------------------
// Canvas texture helpers (lazy: browser only)
// ---------------------------------------------------------------------------

type Ctx2D = CanvasRenderingContext2D;

function makeCanvas(w: number, h: number): HTMLCanvasElement | null {
  if (typeof document === 'undefined') return null;
  const cv = document.createElement('canvas');
  cv.width = w;
  cv.height = h;
  return cv;
}

function toTexture(cv: HTMLCanvasElement, repeat = true): THREE.CanvasTexture {
  const tex = new THREE.CanvasTexture(cv);
  if (repeat) tex.wrapS = THREE.RepeatWrapping;
  if (repeat) tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 4;
  return tex;
}

const texCache = new Map<string, unknown>();
// Keep each procedural texture family under one deterministic key without losing its return type.
function cached<T>(key: string, build: () => T | null): T | null {
  const hit = texCache.get(key) as T | undefined;
  if (hit) return hit;
  const tex = build();
  if (tex) texCache.set(key, tex);
  return tex;
}

/** Soft radial gradient (glow sprites, contact shadows). */
export function radialMap(inner: string, outer: string, size = 256): THREE.CanvasTexture | null {
  return cached(`radial-${inner}-${outer}-${size}`, () => {
    const cv = makeCanvas(size, size);
    if (!cv) return null;
    const g = cv.getContext('2d') as Ctx2D;
    const grd = g.createRadialGradient(size / 2, size / 2, size * 0.03, size / 2, size / 2, size / 2);
    grd.addColorStop(0, inner);
    grd.addColorStop(1, outer);
    g.fillStyle = grd;
    g.fillRect(0, 0, size, size);
    return toTexture(cv, false);
  });
}

/** Fine-grain roughness + bump pair for polymers/rubber/satin. */
export function grainMaps(seed = 7, size = 256): {roughnessMap: THREE.CanvasTexture; bumpMap: THREE.CanvasTexture} | null {
  return cached(`grain-${seed}-${size}`, () => {
    const rc = makeCanvas(size, size);
    const bc = makeCanvas(size, size);
    if (!rc || !bc) return null;
    const rg = rc.getContext('2d') as Ctx2D;
    const bg = bc.getContext('2d') as Ctx2D;
    const rImg = rg.createImageData(size, size);
    const bImg = bg.createImageData(size, size);
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const n = fbm1(x * 0.11 + y * 0.13, seed, 3);
        const fine = hash01(x * 911 + y * 733, seed);
        const rough = 150 + Math.round((n - 0.5) * 90 + (fine - 0.5) * 26);
        const bump = 128 + Math.round((n - 0.5) * 110 + (fine - 0.5) * 40);
        const i = (y * size + x) * 4;
        rImg.data[i] = rImg.data[i + 1] = rImg.data[i + 2] = Math.max(0, Math.min(255, rough));
        rImg.data[i + 3] = 255;
        bImg.data[i] = bImg.data[i + 1] = bImg.data[i + 2] = Math.max(0, Math.min(255, bump));
        bImg.data[i + 3] = 255;
      }
    }
    rg.putImageData(rImg, 0, 0);
    bg.putImageData(bImg, 0, 0);
    return {roughnessMap: toTexture(rc), bumpMap: toTexture(bc)};
  });
}

/** Brushed-metal streaks (roughness variation along one axis). */
export function brushedMaps(seed = 21, size = 256): {roughnessMap: THREE.CanvasTexture; bumpMap: THREE.CanvasTexture} | null {
  return cached(`brushed-${seed}-${size}`, () => {
    const rc = makeCanvas(size, size);
    const bc = makeCanvas(size, size);
    if (!rc || !bc) return null;
    const rg = rc.getContext('2d') as Ctx2D;
    const bg = bc.getContext('2d') as Ctx2D;
    const rnd = mulberry32(seed);
    const streaks: number[] = [];
    for (let i = 0; i < 220; i += 1) streaks.push(rnd());
    const rImg = rg.createImageData(size, size);
    const bImg = bg.createImageData(size, size);
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const s = streaks[Math.floor(hash01(y, seed) * streaks.length)];
        const rough = 120 + Math.round((s - 0.5) * 90 + (hash01(x * 3 + y, seed) - 0.5) * 22);
        const bump = 128 + Math.round((s - 0.5) * 60);
        const i = (y * size + x) * 4;
        rImg.data[i] = rImg.data[i + 1] = rImg.data[i + 2] = Math.max(0, Math.min(255, rough));
        rImg.data[i + 3] = 255;
        bImg.data[i] = bImg.data[i + 1] = bImg.data[i + 2] = Math.max(0, Math.min(255, bump));
        bImg.data[i + 3] = 255;
      }
    }
    rg.putImageData(rImg, 0, 0);
    bg.putImageData(bImg, 0, 0);
    return {roughnessMap: toTexture(rc), bumpMap: toTexture(bc)};
  });
}

/** Dark seabed albedo + bump (sand speckle over soft blotches). */
export function sandMaps(seed = 5, size = 256): {map: THREE.CanvasTexture; bumpMap: THREE.CanvasTexture} | null {
  return cached(`sand-${seed}-${size}`, () => {
    const ac = makeCanvas(size, size);
    const bc = makeCanvas(size, size);
    if (!ac || !bc) return null;
    const ag = ac.getContext('2d') as Ctx2D;
    const bg = bc.getContext('2d') as Ctx2D;
    // base: vertical soft falloff is applied by lighting; keep albedo near-flat
    ag.fillStyle = '#2e3a4c';
    ag.fillRect(0, 0, size, size);
    const rnd = mulberry32(seed);
    for (let i = 0; i < 2600; i += 1) {
      const x = rnd() * size;
      const y = rnd() * size;
      const r = 0.5 + rnd() * 1.6;
      const l = 38 + rnd() * 34;
      ag.fillStyle = `rgba(${Math.round(l)},${Math.round(l + 8)},${Math.round(l + 16)},0.5)`;
      ag.beginPath();
      ag.arc(x, y, r, 0, Math.PI * 2);
      ag.fill();
    }
    // soft large blotches (deterministic)
    for (let i = 0; i < 26; i += 1) {
      const x = hash01(i * 3 + 1, seed) * size;
      const y = hash01(i * 7 + 2, seed) * size;
      const r = 18 + hash01(i, seed + 9) * 42;
      const grd = ag.createRadialGradient(x, y, 1, x, y, r);
      const dark = hash01(i, seed + 4) > 0.5;
      grd.addColorStop(0, dark ? 'rgba(12,18,26,0.35)' : 'rgba(70,88,108,0.28)');
      grd.addColorStop(1, 'rgba(0,0,0,0)');
      ag.fillStyle = grd;
      ag.beginPath();
      ag.arc(x, y, r, 0, Math.PI * 2);
      ag.fill();
    }
    // bump from fine noise
    const bImg = bg.createImageData(size, size);
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const n = fbm1(x * 0.2 + y * 0.23, seed + 2, 3);
        const v = Math.max(0, Math.min(255, Math.round(100 + (n - 0.5) * 120)));
        const i = (y * size + x) * 4;
        bImg.data[i] = bImg.data[i + 1] = bImg.data[i + 2] = v;
        bImg.data[i + 3] = 255;
      }
    }
    bg.putImageData(bImg, 0, 0);
    const map = toTexture(ac);
    map.colorSpace = THREE.SRGBColorSpace;
    return {map, bumpMap: toTexture(bc)};
  }) as {map: THREE.CanvasTexture; bumpMap: THREE.CanvasTexture} | null;
}

/** Soft underwater caustic web (additive overlay, animated via texture offset). */
export function causticMap(seed = 11, size = 256): THREE.CanvasTexture | null {
  return cached(`caustic-${seed}-${size}`, () => {
    const cv = makeCanvas(size, size);
    if (!cv) return null;
    const g = cv.getContext('2d') as Ctx2D;
    const img = g.createImageData(size, size);
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const u = x / size;
        const v = y / size;
        const a = Math.sin((u * 7 + v * 5 + fbm1(u * 9, seed, 3) * 4) * Math.PI);
        const b = Math.sin((v * 8 - u * 4 + fbm1(v * 8, seed + 3, 3) * 4) * Math.PI);
        const web = Math.pow(Math.abs(a * b), 6);
        const val = Math.max(0, Math.min(255, Math.round(web * 200)));
        const i = (y * size + x) * 4;
        img.data[i] = Math.round(val * 0.62);
        img.data[i + 1] = Math.round(val * 0.78);
        img.data[i + 2] = val;
        img.data[i + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
    return toTexture(cv);
  });
}

/** Vertical water-column gradient (dark cinematic). */
export function waterGradientMap(): THREE.CanvasTexture | null {
  return cached('water-gradient', () => {
    const cv = makeCanvas(64, 512);
    if (!cv) return null;
    const g = cv.getContext('2d') as Ctx2D;
    const grd = g.createLinearGradient(0, 0, 0, 512);
    grd.addColorStop(0, '#16344d');
    grd.addColorStop(0.35, '#0a1a2b');
    grd.addColorStop(0.7, '#050b13');
    grd.addColorStop(1, '#02040a');
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 512);
    const tex = toTexture(cv, false);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  });
}

// ---------------------------------------------------------------------------
// PBR material presets (meshPhysicalMaterial props; restrained reflections)
// ---------------------------------------------------------------------------

export type PhysicalMat = {
  color: string;
  roughness: number;
  metalness: number;
  clearcoat?: number;
  clearcoatRoughness?: number;
  roughnessMap?: THREE.Texture;
  bumpMap?: THREE.Texture;
  bumpScale?: number;
  transparent?: boolean;
  opacity?: number;
  emissive?: string;
  emissiveIntensity?: number;
  envMapIntensity?: number;
  ior?: number;
  thickness?: number;
  specularIntensity?: number;
  toneMapped?: boolean;
  side?: THREE.Side;
  depthWrite?: boolean;
};

function withMaps(base: PhysicalMat, maps: {roughnessMap?: THREE.Texture | null; bumpMap?: THREE.Texture | null} | null): PhysicalMat {
  if (!maps) return base;
  const out: PhysicalMat = {...base};
  if (maps.roughnessMap) out.roughnessMap = maps.roughnessMap;
  if (maps.bumpMap) {
    out.bumpMap = maps.bumpMap;
    out.bumpScale = 0.03;
  }
  return out;
}

/** Satin polymer shell: soft clearcoat sheen, never mirror. */
export function pbrSatin(color: string): PhysicalMat {
  return withMaps(
    {
      color,
      roughness: 0.42,
      metalness: 0.05,
      clearcoat: 0.5,
      clearcoatRoughness: 0.38,
      envMapIntensity: 0.4,
    },
    grainMaps(7),
  );
}

/** Matte polymer: flat, light, readable. */
export function pbrMatte(color: string): PhysicalMat {
  return withMaps(
    {
      color,
      roughness: 0.72,
      metalness: 0,
      clearcoat: 0,
      envMapIntensity: 0.2,
    },
    grainMaps(13),
  );
}

/** Rubber cable jacket: high roughness, micro-bump, faint sheen. */
export function pbrRubber(color: string): PhysicalMat {
  return withMaps(
    {
      color,
      roughness: 0.86,
      metalness: 0.02,
      clearcoat: 0.08,
      clearcoatRoughness: 0.7,
      envMapIntensity: 0.25,
    },
    grainMaps(29),
  );
}

/** Brushed light metal: restrained anisotropic feel via streak roughness. */
export function pbrMetal(color: string): PhysicalMat {
  return withMaps(
    {
      color,
      roughness: 0.38,
      metalness: 0.85,
      clearcoat: 0.15,
      clearcoatRoughness: 0.3,
      envMapIntensity: 0.5,
    },
    brushedMaps(21),
  );
}

/** Translucent glass/fiber: physical, low roughness, restrained env response. */
export function pbrGlass(tint: string, opacity = 0.5): PhysicalMat {
  return {
    color: tint,
    roughness: 0.08,
    metalness: 0,
    clearcoat: 1,
    clearcoatRoughness: 0.08,
    transparent: true,
    opacity,
    emissive: tint,
    emissiveIntensity: 0.12,
    envMapIntensity: 0.6,
    ior: 1.45,
    specularIntensity: 1,
    depthWrite: false,
  };
}

/** Pale teaching glass core: translucent but unmistakably present. */
export function pbrCore(color: string, opacity = 0.85): PhysicalMat {
  return {
    color,
    roughness: 0.32,
    metalness: 0,
    clearcoat: 0.25,
    clearcoatRoughness: 0.4,
    transparent: true,
    opacity,
    emissive: color,
    emissiveIntensity: 0.12,
    envMapIntensity: 0.35,
    depthWrite: false,
  };
}

// ---------------------------------------------------------------------------
// Geometry imperfection helpers (deterministic)
// ---------------------------------------------------------------------------

export type Vec3 = [number, number, number];

/** Gently perturb path points so cables/strands avoid a CG-perfect line. */
export function wobblePoints(points: Vec3[], amp = 0.05, freq = 0.8, seed = 3): Vec3[] {
  return points.map((p, i) => {
    const t = (i / Math.max(1, points.length - 1)) * freq * Math.PI * 2;
    const dy = (fbm1(t * 0.7 + 1.3, seed, 3) - 0.5) * 2 * amp;
    const dz = (fbm1(t * 0.7 + 4.1, seed + 5, 3) - 0.5) * 2 * amp;
    return [p[0], p[1] + dy, p[2] + dz];
  });
}

/** Build a CatmullRom curve from path points. */
export function naturalCurve(points: Vec3[]): THREE.CatmullRomCurve3 {
  return new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(p[0], p[1], p[2])), false, 'catmullrom', 0.5);
}

/**
 * Helical armor wrap around a curve (subsea cable steel-wire layer).
 * Returns strand polylines in world space; render as thin tubes.
 */
export function helixAroundCurve(
  curve: THREE.CatmullRomCurve3,
  radius: number,
  wires = 3,
  turns = 26,
  samples = 220,
  phase = 0,
): Vec3[][] {
  const up = new THREE.Vector3(0, 1, 0);
  const out: Vec3[][] = [];
  for (let w = 0; w < wires; w += 1) {
    const line: Vec3[] = [];
    for (let i = 0; i <= samples; i += 1) {
      const u = i / samples;
      const p = curve.getPoint(u);
      const tan = curve.getTangent(u).normalize();
      const side = new THREE.Vector3().crossVectors(tan, up);
      if (side.lengthSq() < 1e-6) side.set(1, 0, 0);
      side.normalize();
      const upv = new THREE.Vector3().crossVectors(side, tan).normalize();
      const a = phase + (w / wires) * Math.PI * 2 + u * turns * Math.PI * 2;
      const ox = Math.cos(a) * radius;
      const oy = Math.sin(a) * radius;
      line.push([p.x + side.x * ox + upv.x * oy, p.y + side.y * ox + upv.y * oy, p.z + side.z * ox + upv.z * oy]);
    }
    out.push(line);
  }
  return out;
}

/**
 * Tube with subtly varying radius (avoids CG-perfect cylinders).
 * radiusFn(u) multiplies the base radius; keep variation within ±6%.
 */
export function variableTubeGeometry(
  curve: THREE.CatmullRomCurve3,
  radiusFn: (u: number) => number,
  baseRadius: number,
  tubularSegments = 120,
  radialSegments = 20,
): THREE.BufferGeometry {
  const frames = curve.computeFrenetFrames(tubularSegments, false);
  const positions: number[] = [];
  const normals: number[] = [];
  const uvs: number[] = [];
  const indices: number[] = [];
  const pt = new THREE.Vector3();
  for (let i = 0; i <= tubularSegments; i += 1) {
    const u = i / tubularSegments;
    curve.getPointAt(u, pt);
    const r = baseRadius * radiusFn(u);
    const N = frames.normals[Math.min(i, tubularSegments)];
    const B = frames.binormals[Math.min(i, tubularSegments)];
    for (let j = 0; j <= radialSegments; j += 1) {
      // NB: match three.js TubeGeometry's ring convention (-cos, +sin) so the
      // triangle winding below yields outward-facing front faces.
      const a = (j / radialSegments) * Math.PI * 2;
      const nx = -Math.cos(a) * N.x + Math.sin(a) * B.x;
      const ny = -Math.cos(a) * N.y + Math.sin(a) * B.y;
      const nz = -Math.cos(a) * N.z + Math.sin(a) * B.z;
      positions.push(pt.x + r * nx, pt.y + r * ny, pt.z + r * nz);
      normals.push(nx, ny, nz);
      uvs.push(u * 8, j / radialSegments);
    }
  }
  for (let i = 0; i < tubularSegments; i += 1) {
    for (let j = 0; j < radialSegments; j += 1) {
      const a = i * (radialSegments + 1) + j;
      const b = (i + 1) * (radialSegments + 1) + j;
      indices.push(a, b, a + 1, b, b + 1, a + 1);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  return geo;
}

/** Gently irregular rock (displaced icosahedron, deterministic). */
export function rockGeometry(r: number, seed: number, detail = 1): THREE.BufferGeometry {
  const geo = new THREE.IcosahedronGeometry(r, detail);
  const pos = geo.getAttribute('position') as THREE.BufferAttribute;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 1) {
    v.fromBufferAttribute(pos, i);
    const n = fbm1(v.x * 1.7 + v.y * 2.3 + v.z * 1.3, seed, 3);
    const s = 1 + (n - 0.5) * 0.42;
    v.multiplyScalar(s);
    pos.setXYZ(i, v.x, v.y * 0.72, v.z);
  }
  geo.computeVertexNormals();
  return geo;
}

// ---------------------------------------------------------------------------
// Cinematic camera helpers (deterministic from frame/time)
// ---------------------------------------------------------------------------

/** Subtle handheld sway added on top of authored camera anchors. */
export function sway3(t: number, amp = 0.05, seed = 1): Vec3 {
  return [
    Math.sin(t * 0.5 + seed) * amp,
    Math.sin(t * 0.37 + seed * 1.7) * amp * 0.7,
    Math.sin(t * 0.43 + seed * 2.3) * amp * 0.5,
  ];
}

export function add3(a: Vec3, b: Vec3): Vec3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

/** 9:16-safe vertical framing constants (fractions of frame height). */
export const CINE = {
  captionBandY: 0.115,
  subjectBandTop: 0.24,
  subjectBandBottom: 0.92,
  glowRestraint: 0.85,
} as const;
