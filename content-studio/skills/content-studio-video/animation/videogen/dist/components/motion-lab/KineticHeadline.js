import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CYAN, MUTED, TEXT } from '../../design/color.js';
const clamp01 = (value) => Math.max(0, Math.min(1, value));
// A cue owns its entire time range, so the headline never depends on render order.
export const activeHeadlineCue = (cues, now) => {
    for (let index = cues.length - 1; index >= 0; index--) {
        if (now >= cues[index].start && now < cues[index].end)
            return cues[index];
    }
    return undefined;
};
export function KineticHeadline({ now, cues, color = TEXT, muted = MUTED, accent = CYAN, fontSize = 54, width = 960, top = 315, selectionHandles = false, }) {
    const cue = activeHeadlineCue(cues, now);
    if (!cue)
        return null;
    // A short cue lead keeps a newly spoken word visible on its boundary frame.
    const reveal = clamp01((now - cue.start + 0.2) / 0.2);
    const exit = clamp01((cue.end - now + 0.1) / 0.1);
    const opacity = Math.min(reveal, exit);
    return (_jsx("div", { style: { position: 'absolute', top, left: '50%', width, transform: `translate(-50%, ${(1 - reveal) * 18}px)`, textAlign: 'center', fontFamily: 'Arial, Helvetica, sans-serif', fontSize, fontWeight: 600, lineHeight: 1.18, opacity, zIndex: 20 }, children: cue.lines.map((line, lineIndex) => (_jsx("div", { style: { minHeight: fontSize * 1.2 }, children: line.map((part, partIndex) => (_jsxs("span", { style: { position: 'relative', color: part.emphasis || part.strong ? color : muted, fontWeight: part.emphasis || part.strong ? 800 : 500, outline: part.emphasis ? `2px solid ${accent}` : undefined, outlineOffset: part.emphasis ? 2 : undefined, whiteSpace: 'pre' }, children: [part.text, part.emphasis && selectionHandles && _jsxs(_Fragment, { children: [_jsx("span", { style: { position: 'absolute', left: -8, top: -10, width: 12, height: 12, borderRadius: '50%', background: accent } }), _jsx("span", { style: { position: 'absolute', right: -8, bottom: -10, width: 12, height: 12, borderRadius: '50%', background: accent } })] })] }, partIndex))) }, lineIndex))) }));
}
