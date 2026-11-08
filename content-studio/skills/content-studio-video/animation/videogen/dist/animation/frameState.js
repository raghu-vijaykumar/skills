// Deterministic Frame State Graph.
//
// resolveFrame(t, inputs) collapses every animation channel for one instant
// into a single, inspectable snapshot: resolved semantic actions, active
// motion, attention + emphasis, camera transform + screen geometry, active
// paths, and typography progress. Remotion scenes and Node validators can both
// consume it — no render needed, no intermediate file.
import { resolveActions, attentionFor } from './choreography.js';
import { cameraTransformAt, applyTransform, visibleRect } from './camera.js';
import { emphasisParams } from './attention.js';
import { mediaFrame } from './media.js';
export function resolveFrame(inputs) {
    const { t, width, height, actions = [], shots = [], geometry = [], paths = [], typography, media = [] } = inputs;
    const resolved = resolveActions(t, actions);
    const active = resolved.filter((action) => action.active);
    const primary = active.filter((action) => action.attention === 'primary');
    const attention = attentionFor(t, actions);
    const camera = cameraTransformAt(t, shots, width, height);
    const visible = visibleRect(camera, width, height);
    const emphasis = new Map();
    for (const [target, level] of attention)
        emphasis.set(target, emphasisParams(level));
    const frameGeometry = geometry.map((g) => {
        const screen = {
            x: applyTransform({ x: g.rect.x, y: g.rect.y }, camera, width, height).x,
            y: applyTransform({ x: g.rect.x, y: g.rect.y }, camera, width, height).y,
            w: g.rect.w * camera.scale,
            h: g.rect.h * camera.scale,
        };
        const tl = applyTransform({ x: g.rect.x, y: g.rect.y }, camera, width, height);
        const br = applyTransform({ x: g.rect.x + g.rect.w, y: g.rect.y + g.rect.h }, camera, width, height);
        const onScreen = br.x > 0 && tl.x < width && br.y > 0 && tl.y < height;
        void screen;
        return { id: g.id, box: { rect: g.rect, screen: { x: tl.x, y: tl.y, w: br.x - tl.x, h: br.y - tl.y }, onScreen } };
    });
    const framePaths = paths.map((fp) => {
        const activeWin = (fp.activeFrom ?? -Infinity) <= t && t < (fp.activeTo ?? Infinity);
        return { id: fp.id, active: activeWin, progress: activeWin ? 0.5 : 0, point: fp.path.pointAt(0.5), bounds: fp.path.bounds() };
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
const samplePointInRect = (p, r, pad) => p.x >= r.x - pad && p.x <= r.x + r.w + pad && p.y >= r.y - pad && p.y <= r.y + r.h + pad;
// A path sampling inside a box it does not connect to is a collision.
export function pathCollisionReport(frame, inputs, pad = 4) {
    const issues = [];
    for (const fp of inputs.paths ?? []) {
        if (!((fp.activeFrom ?? -Infinity) <= frame.t && frame.t < (fp.activeTo ?? Infinity)))
            continue;
        const samples = fp.path.samples(48);
        for (const p of samples) {
            for (const g of inputs.geometry ?? []) {
                if (fp.connects && (g.id === fp.connects.from || g.id === fp.connects.to))
                    continue;
                if (samplePointInRect(p, g.rect, pad)) {
                    issues.push({ t: frame.t, kind: 'error', msg: `path "${fp.id}" crosses geometry "${g.id}"` });
                    break;
                }
            }
        }
    }
    return issues;
}
// Camera motion continuity: sample the resolved trajectory and flag centre
// teleports (large jumps between consecutive samples).
export function cameraContinuityReport(shots, width, height, step = 0.1, maxJump = 60) {
    const issues = [];
    let prev = null;
    for (let t = 0; t <= 120 + 1e-9; t += step) {
        const cam = cameraTransformAt(t, shots, width, height);
        if (prev) {
            const dx = cam.cx - prev.cx;
            const dy = cam.cy - prev.cy;
            const jump = Math.hypot(dx, dy) * prev.scale;
            if (jump > maxJump)
                issues.push({ t, kind: 'warn', msg: `camera centre jumped ${jump.toFixed(0)}px between samples` });
        }
        prev = cam;
    }
    return issues;
}
// Camera-aware readability: any geometry that is expected on screen must not be
// shrunk below `minScale` while a PRIMARY action targets it (unreadable focus).
export function cameraReadabilityReport(frame, inputs, minScale = 0.85) {
    const issues = [];
    const primaryTargets = new Set(frame.primary.map((a) => a.target).filter(Boolean));
    for (const g of frame.geometry) {
        if (primaryTargets.has(g.id) && frame.camera.scale < minScale) {
            issues.push({ t: frame.t, kind: 'warn', msg: `primary "${g.id}" readable only at scale ${frame.camera.scale.toFixed(2)}x (< ${minScale})` });
        }
    }
    return issues;
}
// A PRIMARY action firing while the camera is still far out is a focus conflict.
export function cameraAttentionConflictReport(frame, minScale = 1.0) {
    const issues = [];
    if (frame.primary.length > 0 && frame.camera.scale < minScale) {
        issues.push({ t: frame.t, kind: 'warn', msg: `${frame.primary.length} PRIMARY action(s) while camera is only ${frame.camera.scale.toFixed(2)}x` });
    }
    return issues;
}
