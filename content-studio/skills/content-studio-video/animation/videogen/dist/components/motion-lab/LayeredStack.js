import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { PURPLE } from '../../design/color.js';
const clamp01 = (value) => Math.max(0, Math.min(1, value));
// Separating the cards in screen space makes a system stack legible at portrait size.
export function LayeredStack({ now, start, layers, x = 545, y = 820, width = 440, gap = 92, accent = PURPLE }) {
    const p = clamp01((now - start) / 0.8);
    const spread = p * p * (3 - 2 * p);
    return (_jsx("div", { style: { position: 'absolute', left: x, top: y, width, height: 620, transform: 'translateX(-50%)', perspective: 900 }, children: layers.map((layer, index) => {
            const lift = (layers.length - index - 1) * gap * spread;
            return (_jsxs("div", { style: { position: 'absolute', left: 0, top: 200 + index * 15 - lift, width, height: 105, background: `linear-gradient(135deg, ${layer.color ?? '#24252e'}, #08090e)`, border: '2px solid #777985', borderRadius: 7, boxShadow: '0 16px 25px #0008', transform: 'rotateX(55deg) rotateZ(-14deg)', color: '#fff', padding: '14px 22px', boxSizing: 'border-box' }, children: [_jsx("div", { style: { fontSize: 21, fontWeight: 800 }, children: layer.label }), _jsx("div", { style: { fontSize: 13, color: accent, fontFamily: 'Consolas, monospace' }, children: layer.detail })] }, `${layer.label}-${index}`));
        }) }));
}
