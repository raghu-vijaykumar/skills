import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BORDER, MUTED, PURPLE } from '../../design/color.js';
// Markers are independent of scene components, keeping navigation continuous through cuts.
export function ChapterSpine({ now, markers, dark = true, accent = PURPLE, top = 552, width = 780 }) {
    if (markers.length === 0)
        return null;
    const ink = dark ? MUTED : '#8b8b90';
    const line = dark ? BORDER : '#c8c8cc';
    let active = -1;
    for (let index = 0; index < markers.length; index++) {
        if (now >= markers[index].start)
            active = index;
    }
    return (_jsxs("div", { style: { position: 'absolute', top, left: 48, width, height: 76, fontFamily: 'Consolas, monospace', zIndex: 25 }, children: [_jsx("div", { style: { position: 'absolute', top: 18, left: 0, width: 38, height: 38, borderRadius: 9, background: accent, boxShadow: `0 2px 8px ${accent}66`, color: '#fff', display: 'grid', placeItems: 'center', fontSize: 27, fontWeight: 900 }, children: "\u25B0" }), _jsx("div", { style: { position: 'absolute', left: 42, top: 36, width, height: 2, background: line } }), markers.map((marker, index) => {
                const x = 134 + index * (width - 130) / Math.max(1, markers.length - 1);
                const passed = index <= active;
                return (_jsxs("div", { style: { position: 'absolute', left: x, top: 28, width: 110, transform: 'translateX(-50%)', textAlign: 'center' }, children: [_jsx("div", { style: { width: 16, height: 16, borderRadius: '50%', margin: '0 auto 9px', border: `2px solid ${passed ? accent : line}`, background: passed ? accent : dark ? '#121212' : '#fff', boxSizing: 'border-box' } }), _jsx("div", { style: { fontSize: 14, fontWeight: 800, lineHeight: 1.1, color: passed ? accent : ink, textTransform: 'uppercase' }, children: marker.label })] }, `${marker.label}-${index}`));
            })] }));
}
