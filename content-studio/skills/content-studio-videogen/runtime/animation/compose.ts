// Pure composition helpers for the choreography graph. They deterministically
// rewrite absolute start times of MotionActions so a timeline can express
// sequence / stagger / dependency order without ad-hoc frame arithmetic.
//
// All functions are pure: they never mutate the input actions.

import type {MotionAction} from './types.ts';

export function cloneAction(action: MotionAction): MotionAction {
  return {...action, dependsOn: action.dependsOn ? [...action.dependsOn] : undefined};
}

export function delayed(action: MotionAction, by: number): MotionAction {
  return {...cloneAction(action), start: action.start + by};
}

// Place `action` after `trigger` completes (trigger.start + trigger.duration).
export function after(action: MotionAction, trigger: MotionAction): MotionAction {
  return {...cloneAction(action), start: Math.max(action.start, trigger.start + trigger.duration)};
}

// Lay actions back-to-back starting at `start`, in the given order. Each
// action occupies exactly its own duration; the next starts immediately.
export function sequence(start: number, actions: readonly MotionAction[]): MotionAction[] {
  let cursor = start;
  return actions.map((action) => {
    const next = {...cloneAction(action), start: cursor};
    cursor += action.duration;
    return next;
  });
}

// Assign each action a start of `start + index * step` (relative timing stays).
export function stagger(start: number, step: number, actions: readonly MotionAction[]): MotionAction[] {
  return actions.map((action, index) => ({...cloneAction(action), start: start + index * step}));
}

// Force every action to share the same start (a parallel burst).
export function parallel(start: number, actions: readonly MotionAction[]): MotionAction[] {
  return actions.map((action) => ({...cloneAction(action), start}));
}

// Resolve `dependsOn` references into absolute starts. Each action starts no
// earlier than its own `start` and no earlier than the completion of every
// dependency (dependency.start + dependency.duration). Throws on cycles or
// missing dependencies. Deterministic and independent of the current frame.
export function compileActions(actions: readonly MotionAction[]): MotionAction[] {
  const byId = new Map<string, MotionAction>();
  for (const action of actions) byId.set(action.id, action);

  const resolvedStart = new Map<string, number>();
  const visiting = new Set<string>();
  const done = new Set<string>();

  const resolve = (action: MotionAction): number => {
    const cached = resolvedStart.get(action.id);
    if (cached !== undefined) return cached;
    if (visiting.has(action.id)) {
      throw new Error(`compileActions: dependency cycle at "${action.id}"`);
    }
    visiting.add(action.id);
    let start = action.start;
    for (const depId of action.dependsOn ?? []) {
      const dep = byId.get(depId);
      if (!dep) {
        throw new Error(`compileActions: missing dependency "${depId}" for "${action.id}"`);
      }
      start = Math.max(start, resolve(dep) + dep.duration);
    }
    visiting.delete(action.id);
    done.add(action.id);
    resolvedStart.set(action.id, start);
    return start;
  };

  for (const action of actions) resolve(action);
  return actions.map((action) => ({...action, start: resolvedStart.get(action.id) as number}));
}
