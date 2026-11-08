// Deterministic semantic camera. A camera looks at a point (cx, cy) in canvas
// space at a zoom `scale`. screen = (canvas - center) * scale + viewport/2.
// Ops are semantic (focus/pan/compare/...) and resolve to keyframed transforms
// that any scene or validator can sample — no wall-clock, no hidden state.
import { ease } from './easing.js';
export const identityTransform = (width, height) => ({ cx: width / 2, cy: height / 2, scale: 1 });
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const lerp = (a, b, u) => a + (b - a) * u;
const snap = (v) => {
    const rounded = Number(v.toFixed(12));
    return Math.abs(rounded) < 1e-12 ? 0 : rounded;
};
const cleanTransform = (t) => ({ cx: snap(t.cx), cy: snap(t.cy), scale: snap(t.scale) });
const cleanKey = (k) => ({ t: snap(k.t), ...cleanTransform({ cx: k.cx, cy: k.cy, scale: k.scale }) });
// Scale/center so `region` fits the viewport with a margin, clamped.
export function fitRegion(region, width, height, margin = 0, minScale = 0.5, maxScale = 3) {
    const scale = clamp(Math.min((width - margin * 2) / region.w, (height - margin * 2) / region.h), minScale, maxScale);
    return cleanTransform({ cx: region.x + region.w / 2, cy: region.y + region.h / 2, scale: Math.max(0.05, scale) });
}
export const centerPoint = (region) => ({ x: region.x + region.w / 2, y: region.y + region.h / 2 });
export const unionRects = (regions) => {
    if (regions.length === 0)
        return { x: 0, y: 0, w: 0, h: 0 };
    let x0 = Infinity;
    let y0 = Infinity;
    let x1 = -Infinity;
    let y1 = -Infinity;
    for (const r of regions) {
        x0 = Math.min(x0, r.x);
        y0 = Math.min(y0, r.y);
        x1 = Math.max(x1, r.x + r.w);
        y1 = Math.max(y1, r.y + r.h);
    }
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
};
export const lerpTransform = (a, b, u) => cleanTransform({
    cx: lerp(a.cx, b.cx, u),
    cy: lerp(a.cy, b.cy, u),
    scale: lerp(a.scale, b.scale, u),
});
export function establish(id, region, start, duration = 0.8, width, height, opts = {}) {
    const to = fitRegion(region, width, height, opts.margin ?? 80, opts.minScale, opts.maxScale);
    const keys = [{ t: start, ...identityTransform(width, height) }, { t: snap(start + duration), ...to }].map(cleanKey);
    return { id, op: 'establish', start: snap(start), duration: snap(duration), easing: 'easeOut', region, keys };
}
export function focus(id, region, start, duration = 0.7, width, height, opts = {}) {
    return establish(id, region, start, duration, width, height, { ...opts, margin: opts.margin ?? 120 });
}
export function zoom(id, region, start, duration = 0.9, width, height, opts = {}) {
    const to = fitRegion(region, width, height, opts.margin ?? 10, opts.minScale ?? 1.2, opts.maxScale);
    const keys = [{ t: start, ...identityTransform(width, height) }, { t: snap(start + duration), ...to }].map(cleanKey);
    return { id, op: 'zoom', start: snap(start), duration: snap(duration), easing: 'easeInOut', region, keys };
}
export function pan(id, from, to, start, duration = 1.2, width, height, scale = 1.15) {
    return {
        id,
        op: 'pan',
        start: snap(start),
        duration: snap(duration),
        easing: 'easeInOut',
        keys: [
            { t: snap(start), cx: snap(from.x), cy: snap(from.y), scale: snap(scale) },
            { t: snap(start + duration), cx: snap(to.x), cy: snap(to.y), scale: snap(scale) },
        ].map(cleanKey),
    };
}
export function track(id, waypoints, start, width, height, opts = {}) {
    const keys = waypoints.map((wp) => cleanKey({ t: wp.at, ...fitRegion(wp.region, width, height, opts.margin ?? 120, opts.minScale, opts.maxScale) }));
    return { id, op: 'track', start: snap(start), duration: snap(Math.max(0.001, keys[keys.length - 1].t - keys[0].t)), easing: 'linear', region: waypoints[waypoints.length - 1].region, keys };
}
// Keep a moving target centred: resample its region across time as keyframes.
export function follow(id, regionAt, start, duration, width, height, opts = {}, step = 0.12) {
    const keys = [];
    for (let t = start; t <= start + duration + 1e-6; t += step) {
        keys.push(cleanKey({ t: clamp(t, start, start + duration), ...fitRegion(regionAt(clamp(t, start, start + duration)), width, height, opts.margin ?? 120, opts.minScale, opts.maxScale) }));
    }
    return { id, op: 'follow', start: snap(start), duration: snap(duration), easing: 'linear', keys };
}
export function compare(id, regions, start, duration = 1.0, width, height, opts = {}) {
    const to = fitRegion(unionRects(regions), width, height, opts.margin ?? 120, opts.minScale, opts.maxScale);
    const keys = [{ t: start, ...identityTransform(width, height) }, { t: snap(start + duration), ...to }].map(cleanKey);
    return { id, op: 'compare', start: snap(start), duration: snap(duration), easing: 'easeInOut', region: unionRects(regions), keys };
}
export function cameraReturn(id, start, duration = 0.8, width, height, from) {
    const a = from ?? fitRegion({ x: 0, y: 0, w: width, h: height }, width, height, 0, 1, 1);
    const keys = [{ t: start, ...a }, { t: snap(start + duration), ...identityTransform(width, height) }].map(cleanKey);
    return { id, op: 'return', start: snap(start), duration: snap(duration), easing: 'easeInOut', keys };
}
// ---- Resolution -----------------------------------------------------------
export function cameraTransformAt(now, shots, width, height) {
    let active = null;
    for (const shot of shots) {
        if (now >= shot.start && now < shot.start + shot.duration) {
            if (!active || shot.start >= active.start)
                active = shot;
        }
    }
    if (!active)
        return identityTransform(width, height);
    const keys = active.keys;
    if (now <= keys[0].t)
        return cleanTransform({ cx: keys[0].cx, cy: keys[0].cy, scale: keys[0].scale });
    const last = keys[keys.length - 1];
    if (now >= last.t)
        return cleanTransform({ cx: last.cx, cy: last.cy, scale: last.scale });
    let i = 0;
    while (i < keys.length - 2 && keys[i + 1].t <= now)
        i += 1;
    const a = keys[i];
    const b = keys[i + 1];
    const u = ease(clamp((now - a.t) / Math.max(0.001, b.t - a.t), 0, 1), active.easing);
    return cleanTransform(lerpTransform(a, b, u));
}
export const applyTransform = (p, cam, width, height) => ({
    x: snap((p.x - cam.cx) * cam.scale + width / 2),
    y: snap((p.y - cam.cy) * cam.scale + height / 2),
});
export const invertTransform = (p, cam, width, height) => ({
    x: snap((p.x - width / 2) / cam.scale + cam.cx),
    y: snap((p.y - height / 2) / cam.scale + cam.cy),
});
// CSS for a camera-transformed 2D world of size width×height, applied to the
// world container. It uses `zoom` (a layout re-render) for the scale and
// `translate` for the pan, rather than `transform: scale()`: `zoom` re-lays-out
// and re-rasterizes the content at the target size ("vectorized zoom"), so text
// stays crisp at any zoom instead of resampling a bitmap layer. The pan is
// divided by the scale because `zoom` scales the element's coordinate system.
// Screen position matches `applyTransform`: (x - cx) * scale + width / 2.
export function cameraWorldStyle(cam, width, height) {
    return {
        zoom: cam.scale,
        transform: `translate(${(width / (2 * cam.scale) - cam.cx).toFixed(3)}px, ${(height / (2 * cam.scale) - cam.cy).toFixed(3)}px)`,
        transformOrigin: '0 0',
    };
}
// Canvas-space rect that the viewport currently shows.
export const visibleRect = (cam, width, height) => ({
    x: snap(cam.cx - width / (2 * cam.scale)),
    y: snap(cam.cy - height / (2 * cam.scale)),
    w: snap(width / cam.scale),
    h: snap(height / cam.scale),
});
export const rectInView = (r, cam, width, height) => {
    const v = visibleRect(cam, width, height);
    return r.x < v.x + v.w && r.x + r.w > v.x && r.y < v.y + v.h && r.y + r.h > v.y;
};
// Deterministic checks over the whole camera program: monotonic keyframes,
// sane zoom, one op at a time, no offscreen composition when idle.
export function validateCamera(shots, width, height) {
    const issues = [];
    const sorted = [...shots].sort((a, b) => a.start - b.start);
    for (const shot of sorted) {
        const keys = shot.keys;
        for (let i = 0; i < keys.length - 1; i += 1) {
            if (keys[i + 1].t <= keys[i].t) {
                issues.push({ t: shot.start, shot: shot.id, msg: 'keyframes are not strictly increasing in time', kind: 'error' });
                break;
            }
        }
        for (const k of keys) {
            if (k.scale < 0.02 || k.scale > 50) {
                issues.push({ t: k.t, shot: shot.id, msg: `scale ${k.scale.toFixed(2)} outside sane range`, kind: 'warn' });
            }
        }
        const overlap = sorted.find((other) => other.id !== shot.id && nowRange(shot, other));
        if (overlap)
            issues.push({ t: Math.max(shot.start, overlap.start), shot: shot.id, msg: `overlaps camera shot "${overlap.id}"`, kind: 'warn' });
    }
    return issues;
}
function nowRange(a, b) {
    return a.start < b.start + b.duration && b.start < a.start + a.duration;
}
// Sampled trajectory for validators/paths (centre + scale over time).
export function cameraTrajectory(shots, width, height, step = 0.1) {
    const end = shots.reduce((m, s) => Math.max(m, s.start + s.duration), 0);
    const out = [];
    for (let t = 0; t <= end + 1e-6; t += step)
        out.push({ t, cam: cameraTransformAt(t, shots, width, height) });
    return out;
}
