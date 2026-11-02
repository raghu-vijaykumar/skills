// Revise Labs motion + camera grammar — a curated selection surface over the
// animation core (`src/animation/`). Videos compose beats by selecting named
// transitions from here instead of inventing one-off effects, so the same
// cinematic grammar reads across 2D, 2.5D and 3D scenes.
//
// This module adds no behavior: it only names the canonical vocabulary.

import {
  appear,
  disappear,
  highlight,
  pulse,
  visit,
  mark,
  count,
  draw,
  reveal,
  cameraFocus,
  text,
  shift,
  travel,
  rotate,
  morph,
  split,
  merge,
  shake,
} from '../animation/motion.ts';
import {
  establish,
  focus,
  zoom,
  pan,
  track,
  follow,
  compare,
  cameraReturn,
} from '../animation/camera.ts';
import {
  pushIn,
  pullOut,
  pullBack,
  slide,
  followTarget,
  panBetween,
  handoffFocus,
  arcPan,
  orbit,
  dollyZoom,
  macroMicroMacro,
  impactShake,
  whipPan,
  parallaxDrift,
  sequenceShots,
  snapZoom,
} from '../animation/cameraMoves.ts';
import {visitSequence, processMarks, queueReveal, releaseEdges, compareView} from '../animation/verbs.ts';

// Canonical motion beats.
export const MOTION = {
  enter: appear,
  exit: disappear,
  reveal,
  connect: draw,
  transfer: travel,
  focus: cameraFocus,
  fail: shake,
  success: pulse,
  highlight,
  count,
  morph,
  split,
  merge,
  rotate,
  shift,
  text,
  visit,
  mark,
} as const;

// Canonical camera shots (framing moves).
export const CAMERA = {
  establish,
  focus,
  zoom,
  pan,
  track,
  follow,
  compare,
  cameraReturn,
} as const;

// Extended camera moves for reveals, mechanism and payoff beats.
export const CAMERA_MOVES = {
  pushIn,
  pullOut,
  pullBack,
  slide,
  followTarget,
  panBetween,
  handoffFocus,
  arcPan,
  orbit,
  dollyZoom,
  macroMicroMacro,
  impactShake,
  whipPan,
  parallaxDrift,
  sequenceShots,
  snapZoom,
} as const;

// Composed teaching verbs.
export const VERBS = {
  visitSequence,
  processMarks,
  queueReveal,
  releaseEdges,
  compareView,
} as const;
