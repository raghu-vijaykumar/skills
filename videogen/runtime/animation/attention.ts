// Attention turns the three levels into actual visual emphasis, and exposes a
// deterministic guard so competing PRIMARY moments are caught in validation.

import type {AttentionLevel, MotionAction} from './types.ts';

export const ATTENTION_RANK: Record<AttentionLevel, number> = {background: 0, secondary: 1, primary: 2};

export const attentionOpacity: Record<AttentionLevel, number> = {primary: 1, secondary: 0.92, background: 0.62};

export const attentionBrightness: Record<AttentionLevel, number> = {primary: 1.12, secondary: 1, background: 0.85};

// Focus scale hints scenes can apply to emphasized objects (no layout change).
export const attentionScale: Record<AttentionLevel, number> = {primary: 1, secondary: 1, background: 1};

// Drop-shadow / glow strength for the level (relative to an object glow color).
export const attentionGlow: Record<AttentionLevel, number> = {primary: 1, secondary: 0.5, background: 0};

export type EmphasisParams = {opacity: number; brightness: number; scale: number; glow: number};

export function emphasisParams(level: AttentionLevel): EmphasisParams {
  return {
    opacity: attentionOpacity[level],
    brightness: attentionBrightness[level],
    scale: attentionScale[level],
    glow: attentionGlow[level],
  };
}

// CSS text for the glow of an emphasized object.
export const glowStyle = (glow: number, color: string, radius = 26): string | undefined =>
  glow > 0 ? `0 0 ${Math.round(radius * glow)}px ${color}66` : undefined;

// Given a map of target -> level (as produced by attentionFor/frameState),
// return the params a scene should apply to each target.
export function emphasisForTargets(levels: ReadonlyMap<string, AttentionLevel>): Map<string, EmphasisParams> {
  const out = new Map<string, EmphasisParams>();
  for (const [target, level] of levels) out.set(target, emphasisParams(level));
  return out;
}

// ---- Competing-primary guard -------------------------------------------------

export type AttentionCollision = {t: number; actions: MotionAction[]};

// Sample the whole action timeline; every instant with >1 active PRIMARY
// action is reported. Deterministic, validation-friendly.
export function primaryCollisions(actions: readonly MotionAction[], duration: number, step = 0.1): AttentionCollision[] {
  const collisions: AttentionCollision[] = [];
  for (let t = 0; t <= duration + 1e-9; t += step) {
    const primary = actions.filter((a) => a.attention === 'primary' && t >= a.start && t < a.start + a.duration);
    if (primary.length > 1) collisions.push({t, actions: primary});
  }
  return collisions;
}
