// Deterministic 2.5D depth model. A `DepthCamera` layers perspective and focus
// on top of the flat `CameraTransform` (`cx, cy, scale`), and a `DepthLayer`
// carries a `z` so a scene reads with real parallax, occlusion and soft focus.
//
// The projection is a pure function of (layer, camera, canvas), so the same
// numbers drive every renderer: the DOM renderer draws flat, axis-aligned planes
// at the projected position/scale/blur (visually identical to CSS 3D for these
// billboards), and an R3F backend can place the same plane in front of a real
// PerspectiveCamera using the same `projectLayer`. Node-safe: no DOM, no
// randomness, no wall-clock.

import type {CameraTransform} from './camera.ts';

// A layer placed in the depth space. `x`/`y`/`w`/`h` are canvas units measured
// on the focal plane (`z = 0`); `z` is depth in canvas units, positive toward
// the viewer. Larger `z` = closer = drawn on top = magnified by perspective.
export type DepthLayer = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
};

// Perspective + focus parameters layered on top of a flat camera transform.
export type DepthCamera = {
  /** Perspective focal length (canvas units). Larger = flatter/less perspective. */
  focal: number;
  /** Depth the lens focuses on (canvas units) for soft focus. */
  focusZ: number;
  /** Depth-of-field strength: blur px per canvas-unit of |z - focusZ|. 0 = off. */
  dof: number;
};

export type DepthProjection = {
  x: number; // projected screen origin (px)
  y: number;
  scale: number; // perspective scale (1 at z = 0)
  w: number; // projected width (px)
  h: number;
  zIndex: number; // depth sort key (larger = closer)
  blur: number; // soft-focus blur radius (px)
};

export const DEPTH_DEFAULTS: DepthCamera = {
  focal: 1200,
  focusZ: 0,
  dof: 0.05,
};

// Perspective magnification at a depth: `focal / (focal - z)`. 1 at z = 0,
// > 1 closer to the viewer, < 1 deeper into the scene. This is the single
// source of truth for how depth scales layers in every renderer.
export const perspectiveScale = (z: number, focal: number): number => focal / (focal - z);

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));
const snap = (v: number) => {
  const rounded = Number(v.toFixed(12));
  return Math.abs(rounded) < 1e-12 ? 0 : rounded;
};

// Project a depth layer to screen space. Pure and deterministic.
export function projectLayer(layer: DepthLayer, cam: CameraTransform, depth: Partial<DepthCamera>, width: number, height: number): DepthProjection {
  const d = {...DEPTH_DEFAULTS, ...depth};
  const p = perspectiveScale(layer.z, d.focal);
  const scale = cam.scale * p;
  const blur = Math.max(0, d.dof * Math.abs(layer.z - d.focusZ));
  return {
    x: snap((layer.x - cam.cx) * scale + width / 2),
    y: snap((layer.y - cam.cy) * scale + height / 2),
    scale: snap(scale),
    w: snap(layer.w * scale),
    h: snap(layer.h * scale),
    zIndex: Math.round(layer.z) + 1000,
    blur: snap(blur),
  };
}

// Project many layers and sort them for drawing (far first). The returned array
// is ordered back-to-front so a renderer can iterate without re-sorting.
export function projectLayers(layers: readonly DepthLayer[], cam: CameraTransform, depth: Partial<DepthCamera>, width: number, height: number): {layer: DepthLayer; p: DepthProjection}[] {
  return layers
    .map((layer) => ({layer, p: projectLayer(layer, cam, depth, width, height)}))
    .sort((a, b) => a.layer.z - b.layer.z);
}

// Deterministic "rack focus": sweep `focusZ` from one depth to another over
// [0, 1] progress. Useful for a scene that shifts the viewer's attention
// between a foreground and background layer without moving the camera.
export function rackFocus(fromZ: number, toZ: number, progress: number): number {
  const u = clamp(progress, 0, 1);
  return fromZ + (toZ - fromZ) * u;
}
