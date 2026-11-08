import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CYAN, RED, TEXT } from '../../design/color.js';
// Renderer for the reusable neural-network primitive. It paints one frame of a
// `Network` from a `NetworkState` (see neuralNetwork.ts) as a flat SVG: node
// columns, a representative set of connections, and the forward/backward signal
// travelling through them. The scene owns the camera and any labels.
const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
const mixHex = (a, b, t) => {
    const pa = hex(a);
    const pb = hex(b);
    const u = clamp01(t);
    return `#${pa.map((v, i) => Math.round(v + (pb[i] - v) * u).toString(16).padStart(2, '0')).join('')}`;
};
export function NeuralNetwork({ net, state, width, height, opacity = 1, tone = CYAN, errorTone = RED, weightVisible = false, }) {
    if (opacity < 0.02)
        return null;
    const edges = net.edges.map((e, i) => {
        const a = net.nodes[e.from];
        const b = net.nodes[e.to];
        const flow = state.edgeFlow[i] ?? 0;
        const back = state.edgeBack[i] ?? 0;
        const weight = state.edgeWeight[i] ?? e.weight;
        const base = weightVisible ? 1.2 + weight * 3.4 : 1.8;
        return (_jsx("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: mixHex(tone, errorTone, back * 1.15), strokeWidth: base + flow * 5 + back * 5, strokeLinecap: "round", opacity: opacity * (0.1 + flow * 0.55 + back * 0.6) }, `edge-${e.id}`));
    });
    const nodes = net.nodes.map((n, i) => {
        const act = state.nodeActivation[i] ?? 0;
        const back = state.nodeBack[i] ?? 0;
        const lit = clamp01(act + back);
        const r = n.r * (1 + act * 0.34 + back * 0.22);
        return (_jsxs("g", { children: [_jsx("circle", { cx: n.x, cy: n.y, r: r * 1.7, fill: mixHex(tone, errorTone, back), opacity: opacity * lit * 0.14 }), _jsx("circle", { cx: n.x, cy: n.y, r: r, fill: mixHex(tone, errorTone, back * 1.15), opacity: opacity * (0.34 + lit * 0.62) }), _jsx("circle", { cx: n.x, cy: n.y, r: r * 0.4, fill: TEXT, opacity: opacity * lit * 0.9 })] }, `node-${i}`));
    });
    return (_jsxs("svg", { width: width, height: height, style: { position: 'absolute', inset: 0, pointerEvents: 'none' }, children: [edges, nodes, state.pulse && (_jsxs("g", { children: [_jsx("circle", { cx: state.pulse.x, cy: state.pulse.y, r: 46, fill: tone, opacity: opacity * 0.16 }), _jsx("circle", { cx: state.pulse.x, cy: state.pulse.y, r: 24, fill: tone, opacity: opacity * 0.6 }), _jsx("circle", { cx: state.pulse.x, cy: state.pulse.y, r: 13, fill: TEXT, opacity: opacity * 0.95 })] }))] }));
}
