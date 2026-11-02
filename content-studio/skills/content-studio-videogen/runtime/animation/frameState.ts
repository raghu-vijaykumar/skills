// Deterministic Frame State Graph.
//
// resolveFrame(t, inputs) collapses every animation channel for one instant
// into a single, inspectable snapshot: resolved semantic actions, active
// motion, attention + emphasis, camera transform + screen geometry, active
// paths, and typography progress. Remotion scenes and Node validators can both
// consume it — no render needed, no intermediate file.

import type {AttentionLevel, MotionAction, ResolvedAction} from './types.ts';
import {resolveActions, attentionFor} from './choreography.ts';
import {cameraTransformAt, applyTransform, visibleRect, type CameraShot, type Rect, type CameraTransform} from './camera.ts';
import {emphasisParams, type EmphasisParams} from './attention.ts';
import type {Path} from './path.ts';
import {mediaFrame, type MediaClip} from './media.ts';

export type ScreenBox = {rect: Rect; screen: Rect; onScreen: boolean};

export type FrameGeometry = {id: string; rect: Rect};

export type FramePath = {
  id: string;
  path: Path;
  // Optional active window (default: whole timeline).
  activeFrom?: number;
  activeTo?: number;
  // Geometry ids the path is allowed to touch (its endpoints).
  connects?: {from?: string; to?: string};
};

export type FrameTypography = {id: string; start: number; end: number};

export type FrameInputs = {
  t: number;
  width: number;
  height: number;
  actions?: readonly MotionAction[];
  shots?: readonly CameraShot[];
  geometry?: FrameGeometry[];
  paths?: FramePath[];
  typography?: FrameTypography[];
  media?: readonly MediaClip[];
};

export type ResolvedFrame = {
  t: number;
  width: number;
  height: number;
  resolved: ResolvedAction[];
  active: ResolvedAction[];
  primary: ResolvedAction[];
  attention: Map<string, AttentionLevel>;
  emphasis: Map<string, EmphasisParams>;
  camera: CameraTransform;
  visible: Rect;
  geometry: {id: string; box: ScreenBox}[];
  paths: {
    id: string;
    active: boolean;
    progress: number;
    point: {x: number; y: number};
    bounds: Rect;
  }[];
  typography: {id: string; progress: number}[] | null;
  media: {id: string; kind: MediaClip['kind']; progress: number}[] | null;
};

export function resolveFrame(inputs: FrameInputs): ResolvedFrame {
  const {t, width, height, actions = [], shots = [], geometry = [], paths = [], typography, media = []} = inputs;

  const resolved = resolveActions(t, actions);
  const active = resolved.filter((action) => action.active);
  const primary = active.filter((action) => action.attention === 'primary');
  const attention = attentionFor(t, actions);
  const camera = cameraTransformAt(t, shots, width, height);
  const visible = visibleRect(camera, width, height);
  const emphasis = new Map<string, EmphasisParams>();
  for (const [target, level] of attention) emphasis.set(target, emphasisParams(level));

  const frameGeometry = geometry.map((g) => {
    const screen = {
      x: applyTransform({x: g.rect.x, y: g.rect.y}, camera, width, height).x,
      y: applyTransform({x: g.rect.x, y: g.rect.y}, camera, width, height).y,
      w: g.rect.w * camera.scale,
      h: g.rect.h * camera.scale,
    };
    const tl = applyTransform({x: g.rect.x, y: g.rect.y}, camera, width, height);
    const br = applyTransform({x: g.rect.x + g.rect.w, y: g.rect.y + g.rect.h}, camera, width, height);
    const onScreen = br.x > 0 && tl.x < width && br.y > 0 && tl.y < height;
    void screen;
    return {id: g.id, box: {rect: g.rect, screen: {x: tl.x, y: tl.y, w: br.x - tl.x, h: br.y - tl.y}, onScreen}};
  });

  const framePaths = paths.map((fp) => {
    const activeWin = (fp.activeFrom ?? -Infinity) <= t && t < (fp.activeTo ?? Infinity);
    return {id: fp.id, active: activeWin, progress: activeWin ? 0.5 : 0, point: fp.path.pointAt(0.5), bounds: fp.path.bounds()};
  });

  return {
    t,
    width,
    height,
    resolved,
    active,
    primary,
    attention,
    emphasis,
    camera,
    visible,
    geometry: frameGeometry,
    paths: framePaths,
    typography: typography
      ? typography.map((tp) => ({
          id: tp.id,
          progress: Math.max(0, Math.min(1, (t - tp.start) / Math.max(0.001, tp.end - tp.start))),
        }))
      : null,
    media: media.length > 0 ? mediaFrame(t, media) : null,
  };
}

// ---------------------------------------------------------------------------
// Validation helpers operating on resolved frames.

export type FrameIssue = {t: number; msg: string; kind: 'error' | 'warn'};

const samplePointInRect = (p: {x: number; y: number}, r: Rect, pad: number) => p.x >= r.x - pad && p.x <= r.x + r.w + pad && p.y >= r.y - pad && p.y <= r.y + r.h + pad;

// A path sampling inside a box it does not connect to is a collision.
export function pathCollisionReport(frame: ResolvedFrame, inputs: FrameInputs, pad = 4): FrameIssue[] {
  const issues: FrameIssue[] = [];
  for (const fp of inputs.paths ?? []) {
    if (!((fp.activeFrom ?? -Infinity) <= frame.t && frame.t < (fp.activeTo ?? Infinity))) continue;
    const samples = fp.path.samples(48);
    for (const p of samples) {
      for (const g of inputs.geometry ?? []) {
        if (fp.connects && (g.id === fp.connects.from || g.id === fp.connects.to)) continue;
        if (samplePointInRect(p, g.rect, pad)) {
          issues.push({t: frame.t, kind: 'error', msg: `path "${fp.id}" crosses geometry "${g.id}"`});
          break;
        }
      }
    }
  }
  return issues;
}

// Camera motion continuity: sample the resolved trajectory and flag centre
// teleports (large jumps between consecutive samples).
export function cameraContinuityReport(shots: readonly CameraShot[], width: number, height: number, step = 0.1, maxJump = 60): FrameIssue[] {
  const issues: FrameIssue[] = [];
  let prev: CameraTransform | null = null;
  for (let t = 0; t <= 120 + 1e-9; t += step) {
    const cam = cameraTransformAt(t, shots, width, height);
    if (prev) {
      const dx = cam.cx - prev.cx;
      const dy = cam.cy - prev.cy;
      const jump = Math.hypot(dx, dy) * prev.scale;
      if (jump > maxJump) issues.push({t, kind: 'warn', msg: `camera centre jumped ${jump.toFixed(0)}px between samples`});
    }
    prev = cam;
  }
  return issues;
}

// Camera-aware readability: any geometry that is expected on screen must not be
// shrunk below `minScale` while a PRIMARY action targets it (unreadable focus).
export function cameraReadabilityReport(frame: ResolvedFrame, inputs: FrameInputs, minScale = 0.85): FrameIssue[] {
  const issues: FrameIssue[] = [];
  const primaryTargets = new Set(frame.primary.map((a) => a.target).filter(Boolean) as string[]);
  for (const g of frame.geometry) {
    if (primaryTargets.has(g.id) && frame.camera.scale < minScale) {
      issues.push({t: frame.t, kind: 'warn', msg: `primary "${g.id}" readable only at scale ${frame.camera.scale.toFixed(2)}x (< ${minScale})`});
    }
  }
  return issues;
}

// A PRIMARY action firing while the camera is still far out is a focus conflict.
export function cameraAttentionConflictReport(frame: ResolvedFrame, minScale = 1.0): FrameIssue[] {
  const issues: FrameIssue[] = [];
  if (frame.primary.length > 0 && frame.camera.scale < minScale) {
    issues.push({t: frame.t, kind: 'warn', msg: `${frame.primary.length} PRIMARY action(s) while camera is only ${frame.camera.scale.toFixed(2)}x`});
  }
  return issues;
}
