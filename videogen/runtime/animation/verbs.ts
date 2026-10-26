// Semantic Visual Verbs: small, reusable choreographies composed from the
// existing motion primitives. Deterministic and geometry-free (they operate on
// semantic targets); scenes attach geometry. Not domain presets.

import type {MotionAction} from './types.ts';
import {visit, mark, draw, reveal, highlight} from './motion.ts';
import {stagger} from './compose.ts';
import {compare, type CameraShot, type Rect} from './camera.ts';

// VISIT: visit each target in order (traversal / walkthrough).
export function visitSequence(prefix: string, targets: string[], start: number, step = 0.4): MotionAction[] {
  return stagger(start, step, targets.map((target, i) => visit(`${prefix}-visit-${i}`, target, start, 0.4)));
}

// PROCESS: mark each target processed, one after another.
export function processMarks(prefix: string, targets: string[], start: number, step = 0.5): MotionAction[] {
  return stagger(start, step, targets.map((target, i) => mark(`${prefix}-mark-${i}`, target, start, 0.5)));
}

// QUEUE: reveal targets into a queue, then highlight the front.
export function queueReveal(prefix: string, targets: string[], start: number, step = 0.35): MotionAction[] {
  const actions: MotionAction[] = stagger(start, step, targets.map((target, i) => reveal(`${prefix}-queue-${i}`, target, start, 0.5)));
  if (targets.length > 0) actions.push(highlight(`${prefix}-front`, targets[0], start + step * Math.max(0, targets.length - 1) + 0.3, 0.6, 'primary'));
  return actions;
}

// RELEASE: draw each dependency edge when its source finishes.
export function releaseEdges(prefix: string, edges: {from: string; to: string}[], start: number, per = 0.3): MotionAction[] {
  return edges.map((edge, i) => draw(`${prefix}-release-${i}`, `${edge.from}->${edge.to}`, start + i * per, 0.5));
}

// COMPARE: a camera shot framing both regions side by side.
export function compareView(id: string, regions: Rect[], start: number, duration: number, width: number, height: number): CameraShot {
  return compare(id, regions, start, duration, width, height);
}
