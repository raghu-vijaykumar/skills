import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AbsoluteFill, Img, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { RAPID_TAKE as R } from '../../design/rapidTake.js';
// Reusable primitives for the Rapid Take video style. They deliberately do one
// thing each: a shot, a slam, a source mark, a reaction, an annotation. The
// draft composes them on a 2–5 second beat grid instead of inventing a new
// screen grammar per scene.
export function RapidStage({ children, grid = false }) {
    return _jsxs(AbsoluteFill, { style: { background: R.stage, color: R.text, fontFamily: R.sans, overflow: 'hidden' }, children: [grid ? _jsx("div", { style: { position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: `linear-gradient(${R.rule} 1px, transparent 1px), linear-gradient(90deg, ${R.rule} 1px, transparent 1px)`, backgroundSize: '96px 96px' } }) : null, children] });
}
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' };
export function Slam({ lines, color = R.text, size = 150, align = 'left', top = 0.24, delay = 0, accent }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    return _jsx("div", { style: { position: 'absolute', left: align === 'center' ? 90 : 110, right: 90, top: `${top * 100}%`, display: 'flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : 'flex-start', textAlign: align }, children: lines.map((line, index) => {
            const at = delay + index * 0.09;
            const progress = interpolate(frame / fps, [at, at + 0.18], [0, 1], clamp);
            return _jsx("div", { style: { fontSize: size, lineHeight: 0.94, fontWeight: 900, letterSpacing: '-0.055em', textTransform: 'uppercase', color: index === accent ? R.hot : color, opacity: progress, transform: `translateY(${(1 - progress) * 36}px) scale(${0.92 + progress * 0.08})`, textShadow: index === accent ? `0 0 70px ${R.hot}55` : 'none' }, children: line }, `${line}-${index}`);
        }) });
}
export function StatSlam({ value, label, color = R.zap, size = 300, top = 0.2 }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const pop = interpolate(frame / fps, [0, 0.07, 0.24], [1.3, 0.96, 1], clamp);
    return _jsxs("div", { style: { position: 'absolute', left: 80, right: 80, top: `${top * 100}%`, textAlign: 'center' }, children: [_jsx("div", { style: { fontSize: size, lineHeight: 0.82, fontWeight: 900, letterSpacing: '-0.07em', color, transform: `scale(${pop})`, textShadow: `0 0 90px ${color}66` }, children: value }), _jsx("div", { style: { fontFamily: R.mono, fontSize: 40, letterSpacing: 3, marginTop: 24, color: R.text, textTransform: 'uppercase' }, children: label })] });
}
export function SourceShot({ src, kind = 'image', source, label, startFrom = 0, zoom = 1.05, position = 'center', dim = 0.18, fit = 'cover', children }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const scale = interpolate(frame / fps, [0, 6], [1, zoom], clamp);
    const media = kind === 'video'
        ? _jsx(OffthreadVideo, { src: src, muted: true, startFrom: startFrom, style: { width: '100%', height: '100%', objectFit: fit, objectPosition: position, transform: `scale(${scale})` } })
        : _jsx(Img, { src: src, style: { width: '100%', height: '100%', objectFit: fit, objectPosition: position, transform: `scale(${scale})` } });
    return _jsxs("div", { style: { position: 'absolute', inset: 0, background: R.stage }, children: [_jsx("div", { style: { position: 'absolute', inset: 0, overflow: 'hidden' }, children: media }), _jsx("div", { style: { position: 'absolute', inset: 0, background: `linear-gradient(180deg, rgba(5,5,5,.18) 0%, transparent 32%, rgba(5,5,5,${dim}) 100%)` } }), children, _jsxs("div", { style: { position: 'absolute', left: 30, bottom: 26, display: 'flex', gap: 14, alignItems: 'center', fontFamily: R.mono, fontSize: 24, letterSpacing: 1.5, color: R.text, textShadow: '0 2px 10px #000' }, children: [_jsx("span", { style: { background: R.hot, color: R.onHot, padding: '4px 10px', fontWeight: 800 }, children: "SOURCE" }), _jsx("span", { children: label ? `${label} · ${source}` : source })] })] });
}
export function BrowserFrame({ src, url, x = 90, y = 90, w = 1740, h = 900, dark = false }) {
    return _jsxs("div", { style: { position: 'absolute', left: x, top: y, width: w, height: h, background: dark ? '#16181d' : '#f4f4f2', border: `2px solid ${R.rule}`, boxShadow: '0 30px 90px rgba(0,0,0,.65)', overflow: 'hidden' }, children: [_jsxs("div", { style: { height: 42, display: 'flex', alignItems: 'center', gap: 9, padding: '0 16px', background: dark ? '#22252b' : '#dddcd7', borderBottom: `1px solid ${dark ? '#33373f' : '#c9c8c2'}` }, children: [['#ff5f57', '#febc2e', '#28c840'].map((color) => _jsx("span", { style: { width: 11, height: 11, borderRadius: 99, background: color } }, color)), _jsx("div", { style: { flex: 1, marginLeft: 16, fontFamily: R.mono, fontSize: 17, color: dark ? R.muted : '#555', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }, children: url })] }), _jsx(Img, { src: src, style: { width: '100%', height: `calc(100% - 42px)`, objectFit: 'cover', objectPosition: 'top' } })] });
}
export function MemeCut({ src, label, startFrom = 0, fit = 'cover' }) {
    return _jsxs(AbsoluteFill, { style: { background: R.stage, display: 'flex', alignItems: 'center', justifyContent: 'center' }, children: [_jsx("div", { style: { position: 'absolute', inset: 0, overflow: 'hidden' }, children: _jsx(OffthreadVideo, { src: src, muted: true, startFrom: startFrom, style: { width: '100%', height: '100%', objectFit: fit } }) }), _jsx("div", { style: { position: 'absolute', top: 34, left: 34, background: R.stage, color: R.zap, border: `2px solid ${R.zap}`, padding: '8px 14px', fontFamily: R.mono, fontSize: 24, letterSpacing: 2 }, children: "REACTION \u00B7 NOT EVIDENCE" }), _jsx("div", { style: { position: 'absolute', bottom: 54, left: 60, right: 60, textAlign: 'center', fontFamily: R.sans, fontSize: 72, fontWeight: 900, letterSpacing: '-0.03em', textTransform: 'uppercase', textShadow: '0 6px 34px #000' }, children: label })] });
}
export function Annotation({ kind, x, y, w, h, label, color = R.zap, delay = 0, to }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const p = interpolate(frame / fps, [delay, delay + 0.28], [0, 1], clamp);
    if (kind === 'box')
        return _jsx("div", { style: { position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, border: `7px solid ${color}`, boxShadow: `0 0 24px ${color}66`, clipPath: `inset(0 ${100 - p * 100}% 0 0)` }, children: label ? _jsx("div", { style: { position: 'absolute', left: -7, top: -52, background: color, color: R.stage, fontFamily: R.mono, fontSize: 26, fontWeight: 900, letterSpacing: 1, padding: '4px 10px', whiteSpace: 'nowrap' }, children: label }) : null });
    if (kind === 'underline')
        return _jsx("div", { style: { position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w * p}%`, height: `${h}%`, background: color, transform: 'skewX(-8deg)', transformOrigin: 'left' } });
    if (kind === 'circle')
        return _jsxs("svg", { style: { position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, overflow: 'visible' }, viewBox: "0 0 100 100", preserveAspectRatio: "none", children: [_jsx("ellipse", { cx: "50", cy: "50", rx: "46", ry: "44", fill: "none", stroke: color, strokeWidth: "3.4", strokeLinecap: "round", strokeDasharray: "320", strokeDashoffset: 320 * (1 - p) }), label ? _jsx("text", { x: "4", y: "8", fill: color, fontFamily: R.mono, fontSize: "5.2", fontWeight: "800", children: label }) : null] });
    const target = to ?? [x + w, y + h];
    const dx = target[0] - x;
    const dy = target[1] - y;
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    const length = Math.sqrt(dx * dx + dy * dy);
    return _jsxs("svg", { style: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', overflow: 'visible' }, viewBox: "0 0 100 100", preserveAspectRatio: "none", children: [_jsx("line", { x1: x, y1: y, x2: x + dx * p, y2: y + dy * p, stroke: color, strokeWidth: "1.1", strokeLinecap: "round" }), p > 0.9 ? _jsx("g", { transform: `translate(${target[0]} ${target[1]}) rotate(${angle})`, children: _jsx("polygon", { points: "0,0 -2.6,-1.4 -2.6,1.4", fill: color }) }) : null, label ? _jsx("text", { x: x + dx * 0.45, y: y + dy * 0.45 - 1.4, fill: color, fontFamily: R.mono, fontSize: "4.4", fontWeight: "800", children: label }) : null, _jsx("title", { children: `arrow ${length.toFixed(0)}` })] });
}
export function LowerThird({ left, right, color = R.text }) {
    return _jsxs("div", { style: { position: 'absolute', left: 34, right: 34, bottom: 22, display: 'flex', justifyContent: 'space-between', borderTop: `2px solid ${R.rule}`, paddingTop: 10, fontFamily: R.mono, fontSize: 22, letterSpacing: 1.5, color }, children: [_jsx("span", { children: left }), right ? _jsx("span", { style: { color: R.muted }, children: right }) : null] });
}
export function CutFlash({ color = '#ffffff' }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const opacity = interpolate(frame / fps, [0, 0.045], [0.9, 0], clamp);
    return _jsx(AbsoluteFill, { style: { background: color, opacity, zIndex: 90, pointerEvents: 'none' } });
}
