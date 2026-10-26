import {ease} from './easing.ts';
import type {AttentionLevel, MotionAction, ResolvedAction, TeachingBeat} from './types.ts';

export function actionProgress(now: number, action: MotionAction): number {
  if (now <= action.start) return 0;
  if (now >= action.start + action.duration) return 1;
  return ease((now - action.start) / Math.max(0.001, action.duration), action.easing);
}

export function resolveActions(now: number, actions: readonly MotionAction[]): ResolvedAction[] {
  return actions.map((action) => {
    const progress = actionProgress(now, action);
    return {
      ...action,
      progress,
      active: now >= action.start && now < action.start + action.duration,
      complete: now >= action.start + action.duration,
    };
  });
}

export function resolveBeats(now: number, beats: readonly TeachingBeat[]): TeachingBeat | null {
  return beats.find((beat) => now >= beat.start && now < beat.end) ?? null;
}

export function attentionFor(now: number, actions: readonly MotionAction[]): Map<string, AttentionLevel> {
  const result = new Map<string, AttentionLevel>();
  for (const action of actions) {
    if (now < action.start || now >= action.start + action.duration || !action.target) continue;
    const level = action.attention ?? 'secondary';
    const previous = result.get(action.target);
    const rank = {background: 0, secondary: 1, primary: 2} as const;
    if (!previous || rank[level] > rank[previous]) result.set(action.target, level);
  }
  return result;
}

export function interpolateAction(now: number, action: MotionAction, fallback = 0): number {
  if (action.from == null || action.to == null) return fallback;
  return action.from + (action.to - action.from) * actionProgress(now, action);
}

// ---------------------------------------------------------------------------
// Frame state graph (in-memory). The deterministic per-frame picture of every
// action + attention level, without writing an intermediate file.
// ---------------------------------------------------------------------------

export type FrameState = {
  now: number;
  resolved: ResolvedAction[];
  attention: Map<string, AttentionLevel>;
  active: ResolvedAction[];
  primary: ResolvedAction[];
};

export function frameState(now: number, actions: readonly MotionAction[]): FrameState {
  const resolved = resolveActions(now, actions);
  const active = resolved.filter((action) => action.active);
  const primary = active.filter((action) => action.attention === 'primary');
  return {now, resolved, attention: attentionFor(now, actions), active, primary};
}
