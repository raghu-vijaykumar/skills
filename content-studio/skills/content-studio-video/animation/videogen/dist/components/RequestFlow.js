import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const clamp01 = (v) => Math.max(0, Math.min(1, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeIO = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
export function RequestFlow({ now, waypoints, start, hop, tone = '#1a73e8', arc = 0, trail = true, width = 1080, height = 1920, fontSize = 26, }) {
    if (waypoints.length === 0)
        return null;
    const elapsed = now - start;
    if (elapsed < 0)
        return null;
    const last = waypoints.length - 1;
    const idx = Math.min(last, Math.floor(elapsed / Math.max(0.001, hop)));
    const u = clamp01((elapsed - idx * hop) / Math.max(0.001, hop));
    const a = waypoints[idx];
    const b = waypoints[Math.min(idx + 1, last)];
    const e = easeIO(u);
    const px = lerp(a.x, b.x, e);
    const py = lerp(a.y, b.y, e) - Math.sin(e * Math.PI) * arc;
    const settled = idx === last && u > 0.75;
    return (_jsxs(_Fragment, { children: [trail && (_jsxs("svg", { width: width, height: height, style: { position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none', zIndex: 380 }, children: [idx > 0 && (_jsx("polyline", { points: waypoints.slice(0, idx + 1).map((w) => `${w.x},${w.y}`).join(' '), fill: "none", stroke: tone, strokeWidth: 3, strokeDasharray: "9 7", opacity: 0.5 })), _jsx("line", { x1: a.x, y1: a.y, x2: px, y2: py, stroke: tone, strokeWidth: 3, opacity: 0.8 })] })), _jsx("div", { style: { position: 'absolute', left: px, top: py, transform: 'translate(-50%,-50%)', zIndex: 400 }, children: _jsxs("div", { style: {
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        background: settled ? '#12161b' : '#ffffff',
                        border: `2px solid ${tone}`,
                        borderRadius: 12,
                        padding: '7px 16px',
                        boxShadow: `0 10px 26px rgba(20,26,36,0.28), 0 0 0 ${settled ? 4 : 0}px ${tone}22`,
                        whiteSpace: 'nowrap',
                    }, children: [_jsx("span", { style: { width: 10, height: 10, borderRadius: 5, background: tone } }), _jsx("span", { style: { fontSize, fontWeight: 900, fontFamily: "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace", color: settled ? '#ffffff' : '#12161b' }, children: a.label })] }) })] }));
}
