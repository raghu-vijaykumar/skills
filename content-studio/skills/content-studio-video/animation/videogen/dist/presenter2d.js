import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useId } from 'react';
import { smooth } from './components/motion-lab/objectMotion.js';
const leftRest = { elbow: [-132, 100], wrist: [-119, 155], angle: -14, hand: 'rest' };
const rightRest = { elbow: [132, 100], wrist: [119, 155], angle: 14, hand: 'rest' };
const poseLibrary = {
    rest: { head: 0, left: leftRest, right: rightRest },
    'point-left': { head: -6, left: { elbow: [-137, 89], wrist: [-185, 18], angle: -92, hand: 'point' }, right: rightRest },
    'point-right': { head: 6, left: leftRest, right: { elbow: [137, 89], wrist: [185, 18], angle: 92, hand: 'point' } },
    explain: { head: 3, left: { elbow: [-141, 108], wrist: [-175, 42], angle: -30, hand: 'open' },
        right: { elbow: [141, 108], wrist: [175, 42], angle: 30, hand: 'open' } },
    two: { head: -2, left: leftRest, right: { elbow: [139, 98], wrist: [158, 17], angle: 17, hand: 'two' } },
    present: { head: 4, left: leftRest, right: { elbow: [135, 103], wrist: [189, 53], angle: 73, hand: 'open' } },
};
const defaultPalette = { skin: '#e8a877', skinShade: '#a9634c', shirt: '#b64049', shirtShade: '#743344' };
const mix = (a, b, t) => t === 1 ? b : a + (b - a) * t;
const mixPoint = (a, b, t) => [mix(a[0], b[0], t), mix(a[1], b[1], t)];
const fingerPresets = {
    rest: [.38, .28, .24, .22, .22],
    point: [.54, 1, .22, .2, .2],
    open: [.87, .96, 1, .94, .9],
    two: [.48, .96, 1, .24, .22],
};
function mixArm(a, b, t) {
    const arm = { elbow: mixPoint(a.elbow, b.elbow, t), wrist: mixPoint(a.wrist, b.wrist, t),
        angle: mix(a.angle, b.angle, t), hand: t < 0.55 ? a.hand : b.hand };
    if (a.fingers || b.fingers) {
        const from = a.fingers ?? fingerPresets[a.hand];
        const to = b.fingers ?? fingerPresets[b.hand];
        arm.fingers = [mix(from[0], to[0], t), mix(from[1], to[1], t), mix(from[2], to[2], t),
            mix(from[3], to[3], t), mix(from[4], to[4], t)];
    }
    return arm;
}
function transition(from, to, start, duration, frame) {
    const amount = smooth(frame, start, start + duration);
    const pose = { head: mix(from.head, to.head, amount),
        left: mixArm(from.left, to.left, amount), right: mixArm(from.right, to.right, amount) };
    if (from.gaze || to.gaze)
        pose.gaze = mixPoint(from.gaze ?? [from.head / 6, 0], to.gaze ?? [to.head / 6, 0], amount);
    return pose;
}
/** Each cue starts from the pose already visible on that frame. */
export function samplePresenterPose(cues, frame) {
    let from = poseLibrary.rest;
    let to = from;
    let start = 0;
    let duration = 0;
    for (const cue of cues) {
        if (cue.frame > frame)
            break;
        from = transition(from, to, start, duration, cue.frame);
        const base = poseLibrary[cue.gesture];
        // Override the target so a cut or interruption can sample the same pose independently.
        to = cue.pose ? { ...base, ...cue.pose, left: { ...base.left, ...cue.pose.left },
            right: { ...base.right, ...cue.pose.right } } : base;
        start = cue.frame;
        duration = cue.transitionFrames ?? 8;
    }
    return transition(from, to, start, duration, frame);
}
const hands = {
    rest: 'M-8 9Q-17 3-15-10Q-12-20 0-20Q13-19 14-9L12 4Q7 10-8 9Z',
    point: 'M-10 10Q-19 3-13-8L-7-13L-8-31Q-8-39-3-40Q3-41 4-34L5-17Q13-20 16-12L17-2Q15 12 5 13Z',
    two: 'M-11 11Q-18 4-15-8L-10-14L-13-32Q-14-39-9-40Q-4-41-3-34L1-23L5-40Q6-46 12-44Q17-43 15-37L12-18Q19-18 18-10L17 0Q15 13 6 13Z',
    open: 'M-14 11Q-17 8-17 1L-18-13Q-18-19-13-18L-10-12L-10-29Q-9-35-5-34L-2-31L0-37Q3-43 7-39L8-34Q11-38 15-35L15-30Q21-31 22-25L21-10Q20 10 10 13Z',
};
function ArmArt({ side, arm, palette, skin, shirt }) {
    const shoulder = [side * 93, 43];
    const elbow = arm.elbow;
    const wrist = arm.wrist;
    const sleeve = mixPoint(shoulder, elbow, 0.45);
    const armLine = `M${shoulder.join(' ')} Q${elbow[0] - side * 12} ${elbow[1] + 3} ${elbow.join(' ')} Q${elbow[0] + side * 8} ${elbow[1] - 12} ${wrist.join(' ')}`;
    return _jsxs("g", { children: [_jsx("path", { d: armLine, fill: "none", stroke: palette.skinShade, strokeWidth: 30, strokeLinecap: "round" }), _jsx("path", { d: armLine, fill: "none", stroke: skin, strokeWidth: 26, strokeLinecap: "round" }), _jsx("path", { d: `M${shoulder.join(' ')} L${sleeve.join(' ')}`, stroke: shirt, strokeWidth: 42, strokeLinecap: "round" }), _jsxs("g", { transform: `translate(${wrist.join(' ')}) rotate(${arm.angle}) scale(${side} 1)`, children: [_jsx("path", { d: hands[arm.hand], fill: skin, stroke: palette.skinShade, strokeWidth: 1.8, strokeLinejoin: "round" }), _jsx("path", { d: "M-6-6Q0-12 8-7M-2 3Q4 0 9 0", stroke: palette.skinShade, strokeWidth: 1.7, fill: "none", opacity: ".6", strokeLinecap: "round" })] })] });
}
function DefaultBody({ left, right, palette }) {
    const id = useId().replace(/[^\w-]/g, '');
    const skin = `url(#${id}-skin)`;
    const shirt = `url(#${id}-shirt)`;
    return _jsxs(_Fragment, { children: [_jsxs("defs", { children: [_jsxs("linearGradient", { id: `${id}-skin`, x1: "0%", y1: "0%", x2: "90%", y2: "100%", children: [_jsx("stop", { stopColor: palette.skin }), _jsx("stop", { offset: "1", stopColor: palette.skinShade })] }), _jsxs("linearGradient", { id: `${id}-shirt`, gradientUnits: "userSpaceOnUse", x1: -92, y1: 23, x2: 121, y2: 200, children: [_jsx("stop", { stopColor: palette.shirt }), _jsx("stop", { offset: "1", stopColor: palette.shirtShade })] })] }), _jsx("path", { d: "M-126 200L-118 76Q-109 26-54 16H54Q109 26 118 76L126 200Z", fill: shirt, stroke: palette.shirtShade, strokeWidth: 2.5 }), _jsx(ArmArt, { side: -1, arm: left, palette: palette, skin: skin, shirt: shirt }), _jsx(ArmArt, { side: 1, arm: right, palette: palette, skin: skin, shirt: shirt }), _jsx("path", { d: "M-30-16H30L38 32Q0 62-38 32Z", fill: skin, stroke: palette.skinShade, strokeWidth: 2 }), _jsx("path", { d: "M-49 31Q0 80 49 31", fill: "none", stroke: palette.shirtShade, strokeWidth: 12 }), _jsx("path", { d: "M-47 35Q0 75 47 35", fill: "none", stroke: palette.shirt, strokeWidth: 3 }), _jsx("path", { d: "M-103 111L-93 194M102 107L94 194", fill: "none", stroke: palette.shirtShade, strokeWidth: 2, opacity: ".45" })] });
}
/** SVG group anchored at the base of the head. Put it inside the scene SVG. */
export function Presenter2D({ frame, face: Face, body: Body = DefaultBody, cues = [], blinkFrames = [], speech = 0, mouthOpen, x = 0, y = 0, scale = 1, palette: paletteOverride }) {
    const palette = { ...defaultPalette, ...paletteOverride };
    const pose = samplePresenterPose(cues, frame);
    const eyeOpen = blinkFrames.reduce((open, blink) => Math.min(open, Math.max(0.04, Math.abs(frame - blink) / 3)), 1);
    const mouth = Math.max(0, Math.min(1, mouthOpen ?? speech));
    return _jsxs("g", { transform: `translate(${x} ${y}) scale(${scale})`, "data-presenter": "2d", children: [_jsx(Body, { left: pose.left, right: pose.right, palette: palette }), _jsx("g", { transform: `rotate(${pose.head} 0 4)`, children: _jsx(Face, { eyeOpen: eyeOpen, mouthOpen: mouth, gaze: pose.gaze?.[0] ?? pose.head / 6, gazeY: pose.gaze?.[1], palette: palette }) })] });
}
