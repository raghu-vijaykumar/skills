import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AbsoluteFill, useCurrentFrame } from 'remotion';
const DEFAULT_COLOR = '#106A60';
const DEFAULT_ACCENT = '#FFB54A';
const DEFAULT_FLASH = '#F6EDE0';
const clamp01 = (value) => Math.max(0, Math.min(1, value));
// The last frame reaches exactly 1, so a transition cannot leave a one-frame seam.
export function vlogProgress(frame, durationInFrames) {
    if (!Number.isInteger(durationInFrames) || durationInFrames < 2) {
        throw new Error('durationInFrames must be an integer of at least 2');
    }
    return clamp01(frame / (durationInFrames - 1));
}
// A short full-cover hold hides a cut even when it falls between output frames.
export const midPeak = (progress) => clamp01(Math.min(clamp01(progress), 1 - clamp01(progress)) / 0.42);
export function swipeOffset(progress) {
    const p = clamp01(progress);
    if (p === 0)
        return -100;
    if (p === 1)
        return 100;
    if (p < 0.42)
        return -100 + 100 * p / 0.42;
    if (p <= 0.58)
        return 0;
    return 100 * (p - 0.58) / 0.42;
}
/** Mount inside a Sequence so the effect uses that Sequence's local frame. */
export function VlogEffect({ preset, durationInFrames, color, accent = DEFAULT_ACCENT }) {
    const progress = vlogProgress(useCurrentFrame(), durationInFrames);
    const ink = color ?? (preset === 'flash' ? DEFAULT_FLASH : DEFAULT_COLOR);
    const surface = { pointerEvents: 'none', overflow: 'hidden' };
    if (preset === 'flash') {
        return _jsx(AbsoluteFill, { style: { ...surface, backgroundColor: ink, opacity: midPeak(progress) } });
    }
    if (preset === 'swipe') {
        return _jsx(AbsoluteFill, { style: surface, children: _jsx(AbsoluteFill, { style: { backgroundColor: ink, transform: `translateX(${swipeOffset(progress)}%)` }, children: _jsx("div", { style: { position: 'absolute', right: 0, top: 0, bottom: 0, width: '2.5%', backgroundColor: accent } }) }) });
    }
    if (preset === 'shutter') {
        const closure = midPeak(progress);
        return _jsxs(AbsoluteFill, { style: surface, children: [_jsx("div", { style: { position: 'absolute', inset: '0 0 50% 0', backgroundColor: ink,
                        transform: `translateY(${-100 + 100 * closure}%)` } }), _jsx("div", { style: { position: 'absolute', inset: '50% 0 0 0', backgroundColor: ink,
                        transform: `translateY(${100 - 100 * closure}%)` } }), _jsx("div", { style: { position: 'absolute', left: 0, right: 0, top: '49.3%', height: '1.4%',
                        backgroundColor: accent, opacity: Math.max(0, 1 - Math.abs(progress - 0.5) * 12) } })] });
    }
    if (preset === 'speed-lines') {
        return _jsx(AbsoluteFill, { style: surface, children: Array.from({ length: 6 }, (_, index) => _jsx("div", { style: {
                    position: 'absolute', left: `${-45 + 190 * progress + index * 2}%`,
                    top: `${14 + index * 14}%`, width: '38%', height: '2.5%',
                    backgroundColor: index % 2 ? accent : ink,
                    clipPath: 'polygon(5% 0, 100% 0, 95% 100%, 0 100%)',
                    opacity: midPeak(progress) * 0.82,
                } }, index)) });
    }
    // Bars arrive independently and release before the Sequence ends.
    const entered = clamp01(progress / 0.3);
    const opacity = clamp01((1 - progress) / 0.25);
    return _jsxs(AbsoluteFill, { style: { ...surface, opacity }, children: [_jsx("div", { style: { position: 'absolute', top: 0, left: 0, right: 0, height: '2%',
                    backgroundColor: accent, transform: `translateX(${-100 + 100 * entered}%)` } }), _jsx("div", { style: { position: 'absolute', bottom: 0, left: 0, right: 0, height: '2%',
                    backgroundColor: accent, transform: `translateX(${100 - 100 * entered}%)` } }), _jsx("div", { style: { position: 'absolute', top: 0, bottom: 0, left: 0, width: '2%',
                    backgroundColor: accent, transform: `translateY(${-100 + 100 * entered}%)` } }), _jsx("div", { style: { position: 'absolute', top: 0, bottom: 0, right: 0, width: '2%',
                    backgroundColor: accent, transform: `translateY(${100 - 100 * entered}%)` } })] });
}
/** Both scene nodes must cover the composition for the transition window. */
export function VlogTransition({ preset, durationInFrames, from, to, direction = 'left', color = DEFAULT_FLASH, accent = DEFAULT_ACCENT }) {
    const progress = vlogProgress(useCurrentFrame(), durationInFrames);
    const sign = direction === 'left' ? -1 : 1;
    const cover = { overflow: 'hidden' };
    if (preset === 'crossfade') {
        return _jsxs(AbsoluteFill, { style: cover, children: [_jsx(AbsoluteFill, { children: from }), _jsx(AbsoluteFill, { style: { opacity: progress }, children: to })] });
    }
    if (preset === 'slide') {
        return _jsxs(AbsoluteFill, { style: cover, children: [_jsx(AbsoluteFill, { style: { transform: `translateX(${sign * progress * 100}%)` }, children: from }), _jsx(AbsoluteFill, { style: { transform: `translateX(${-sign * (1 - progress) * 100}%)` }, children: to })] });
    }
    if (preset === 'wipe') {
        const inset = direction === 'left'
            ? `inset(0 ${100 * (1 - progress)}% 0 0)`
            : `inset(0 0 0 ${100 * (1 - progress)}%)`;
        return _jsxs(AbsoluteFill, { style: cover, children: [_jsx(AbsoluteFill, { children: from }), _jsx(AbsoluteFill, { style: { clipPath: inset }, children: to }), _jsx("div", { style: { position: 'absolute', top: 0, bottom: 0,
                        left: direction === 'left' ? `${progress * 100}%` : `${(1 - progress) * 100}%`,
                        width: '1.2%', backgroundColor: accent, transform: 'translateX(-50%)' } })] });
    }
    // A full flash at the midpoint hides the hard switch between scene nodes.
    return _jsxs(AbsoluteFill, { style: cover, children: [_jsx(AbsoluteFill, { children: progress < 0.5 ? from : to }), _jsx(AbsoluteFill, { style: { backgroundColor: color, opacity: midPeak(progress), pointerEvents: 'none' } })] });
}
