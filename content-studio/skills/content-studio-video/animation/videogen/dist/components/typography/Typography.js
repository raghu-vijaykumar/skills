import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ease } from '../../animation/easing.js';
import { emphasisParams } from '../../animation/attention.js';
import { CYAN, MUTED, SURFACE_PILL, TEXT } from '../../design/color.js';
import { FONT_MONO } from '../../design/typography.js';
const MONO = FONT_MONO;
const clamp01 = (v) => Math.max(0, Math.min(1, v));
// Resolve a span's eased progress from `now` (deterministic, cue-derived).
export const spanProgress = (now, timing) => clamp01((now - timing.start) / Math.max(0.001, timing.end - timing.start));
// Word-by-word reveal driven by generated narration timing. Spoken words light
// up as the cue advances; the current word is emphasised.
export function WordReveal({ text, now, start, end, fontSize = 40, color = TEXT, muted = MUTED, accent, lineHeight = 1.3, }) {
    const words = text.split(/\s+/);
    const spoken = Math.min(words.length, Math.max(0, Math.floor(spanProgress(now, { start, end }) * words.length)));
    return (_jsx("span", { style: { lineHeight }, children: words.map((word, index) => {
            const done = index < spoken;
            const current = index === spoken;
            return (_jsxs("span", { style: {
                    fontSize,
                    fontWeight: 800,
                    color: current && accent ? accent : done || current ? color : muted,
                    opacity: done || current ? 1 : 0.45,
                    background: current ? SURFACE_PILL : 'transparent',
                    padding: current ? '2px 6px' : 0,
                    borderRadius: 6,
                }, children: [word, ' '] }, `${word}-${index}`));
        }) }));
}
export function PhraseReveal({ children, now, start, duration = 0.5, rise = 12, }) {
    const p = clamp01((now - start) / Math.max(0.001, duration));
    return (_jsx("span", { style: { display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * rise}px)` }, children: children }));
}
// Emphasis applied from an attention level (primary/secondary/background).
export function Emphasis({ children, level, glowColor, style, }) {
    const params = emphasisParams(level);
    const glow = params.glow > 0 ? `0 0 ${Math.round(26 * params.glow)}px ${glowColor}66` : undefined;
    return (_jsx("span", { style: {
            ...style,
            display: 'inline-block',
            opacity: params.opacity,
            filter: `brightness(${params.brightness})`,
            textShadow: glow,
        }, children: children }));
}
// Counter that eases 0 -> value inside [start, end]; value changes are smooth.
export function CountUp({ value, now, start, duration = 0.6, easing = 'easeOut', style, }) {
    const p = clamp01((now - start) / Math.max(0.001, duration));
    const shown = Math.round(value * ease(p, easing));
    return _jsx("span", { style: { ...style, fontFamily: MONO }, children: shown });
}
// Line-by-line code highlight. `activeLine` (or derived from `start` + step)
// drives which line is emphasised. Indentation is preserved verbatim.
export function CodeHighlight({ lines, activeLine, now, start = 0, step = 0.4, fontSize = 20, activeColor = CYAN, muted = MUTED, textColor = TEXT, lineHeight = 1.45, }) {
    const derived = now != null && start != null ? Math.min(lines.length - 1, Math.floor((now - start) / (step ?? 0.4))) : 0;
    const active = activeLine ?? Math.max(0, derived);
    return (_jsx("div", { style: { whiteSpace: 'pre', fontSize, fontWeight: 900, lineHeight, fontFamily: MONO }, children: lines.map((line, index) => {
            const isActive = index === active;
            return (_jsx("div", { style: {
                    color: isActive ? activeColor : textColor,
                    opacity: isActive ? 1 : 0.6,
                    background: isActive ? `${activeColor}18` : 'transparent',
                    borderRadius: 4,
                    padding: '0 8px',
                    width: 'fit-content',
                }, children: line }, `${index}`));
        }) }));
}
export { MONO };
