import { ease } from './easing.js';
export function actionProgress(now, action) {
    if (now <= action.start)
        return 0;
    if (now >= action.start + action.duration)
        return 1;
    return ease((now - action.start) / Math.max(0.001, action.duration), action.easing);
}
export function resolveActions(now, actions) {
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
export function resolveBeats(now, beats) {
    return beats.find((beat) => now >= beat.start && now < beat.end) ?? null;
}
export function attentionFor(now, actions) {
    const result = new Map();
    for (const action of actions) {
        if (now < action.start || now >= action.start + action.duration || !action.target)
            continue;
        const level = action.attention ?? 'secondary';
        const previous = result.get(action.target);
        const rank = { background: 0, secondary: 1, primary: 2 };
        if (!previous || rank[level] > rank[previous])
            result.set(action.target, level);
    }
    return result;
}
export function interpolateAction(now, action, fallback = 0) {
    if (action.from == null || action.to == null)
        return fallback;
    return action.from + (action.to - action.from) * actionProgress(now, action);
}
export function frameState(now, actions) {
    const resolved = resolveActions(now, actions);
    const active = resolved.filter((action) => action.active);
    const primary = active.filter((action) => action.attention === 'primary');
    return { now, resolved, attention: attentionFor(now, actions), active, primary };
}
