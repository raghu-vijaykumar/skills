export function appear(id, target, start, duration = 0.32, attention = 'secondary') {
    return { id, kind: 'appear', target, start, duration, from: 0, to: 1, easing: 'easeOut', attention };
}
export function disappear(id, target, start, duration = 0.28, attention = 'background') {
    return { id, kind: 'disappear', target, start, duration, from: 1, to: 0, easing: 'easeIn', attention };
}
export function highlight(id, target, start, duration = 0.45, attention = 'primary') {
    return { id, kind: 'highlight', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
export function pulse(id, target, start, duration = 0.5, attention = 'secondary') {
    return { id, kind: 'pulse', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
export function visit(id, target, start, duration = 0.38) {
    return { id, kind: 'visit', target, start, duration, from: 0, to: 1, easing: 'easeOut', attention: 'primary' };
}
export function mark(id, target, start, duration = 0.3) {
    return { id, kind: 'mark', target, start, duration, from: 0, to: 1, easing: 'easeOut', attention: 'secondary' };
}
export function count(id, target, start, duration = 0.5) {
    return { id, kind: 'count', target, start, duration, from: 0, to: 1, easing: 'easeOut', attention: 'primary' };
}
// Draw an edge / outline / underline from 0 to 1 (used for tree edges, split
// markers, growth strokes). Progress is interpolation of `from -> to`.
export function draw(id, target, start, duration = 0.4, attention = 'secondary') {
    return { id, kind: 'draw', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
// Reveal a value / glyph / code element (fade + scale-in on arrival).
export function reveal(id, target, start, duration = 0.4, attention = 'secondary') {
    return { id, kind: 'reveal', target, start, duration, from: 0, to: 1, easing: 'backOut', attention };
}
export function cameraFocus(id, target, start, duration = 0.55) {
    return { id, kind: 'camera-focus', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention: 'primary' };
}
export function text(id, target, start, duration = 0.45, attention = 'secondary') {
    return { id, kind: 'text', target, start, duration, from: 0, to: 1, easing: 'easeOut', attention };
}
export function shift(id, target, start, duration, from, to, easing = 'easeInOut') {
    return { id, kind: 'move', target, start, duration, from, to, easing, attention: 'primary' };
}
// Semantic travel between two geometry anchors: `from`/`to` are progress 0..1
// along the segment anchored by the target's own geometry resolver. Scenes use
// this as the deterministic source for moving markers/pointers.
export function travel(id, target, start, duration = 0.5, from = 0, to = 1, easing = 'easeInOut') {
    return { id, kind: 'move', target, start, duration, from, to, easing, attention: 'primary' };
}
// Rotate by degrees (from -> to). Progress interpolates between them.
export function rotate(id, target, start, duration, fromDeg = 0, toDeg = 360, attention = 'secondary') {
    return { id, kind: 'rotate', target, start, duration, from: fromDeg, to: toDeg, easing: 'easeInOut', attention };
}
// Geometry morph (shape A -> shape B). Numeric 0..1 progress; the scene
// resolves both shapes and blends them deterministically.
export function morph(id, target, start, duration = 0.6, attention = 'secondary') {
    return { id, kind: 'morph', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
// Split / merge a composed object into/from its parts (0..1 progress).
export function split(id, target, start, duration = 0.55, attention = 'primary') {
    return { id, kind: 'split', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
export function merge(id, target, start, duration = 0.55, attention = 'primary') {
    return { id, kind: 'merge', target, start, duration, from: 0, to: 1, easing: 'easeInOut', attention };
}
// Shake with a deterministic decaying amplitude (from amplitude -> 0). Scenes
// turn `progress` into a bounded offset (e.g. sin-based, amplitude-scaled).
export function shake(id, target, start, duration = 0.4, amplitude = 12, attention = 'primary') {
    return { id, kind: 'shake', target, start, duration, from: amplitude, to: 0, easing: 'easeOut', attention };
}
