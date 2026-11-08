import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { emphasisParams } from '../../animation/attention.js';
import { buildPath } from '../../animation/path.js';
import { BG_ELEVATED, BORDER, BORDER_DIM, CYAN, GREEN, MUTED, RED, SURFACE_FAINT, SURFACE_PANEL, TEXT, YELLOW } from '../../design/color.js';
import { FONT_MONO } from '../../design/typography.js';
const clamp01 = (v) => Math.max(0, Math.min(1, v));
const CARD_TEXT = TEXT;
const CARD_MUTED = MUTED;
const MONO = FONT_MONO;
// Semantic node/job card with attention emphasis, optional badge/order/ring.
export function NodeCard({ p, label, state, badge, order, ring, shake, dim, appear = 1, width = 168, height = 56, fontSize = 26, solid = false, }) {
    const color = state === 'done' || state === 'ready' ? GREEN : state === 'stuck' ? RED : CYAN;
    const border = state === 'stuck' ? RED : state === 'done' ? GREEN : state === 'ready' ? GREEN : '#30363d';
    const params = emphasisParams(dim ? 'background' : state === 'ready' ? 'secondary' : 'primary');
    const shakeX = shake ? Math.sin(shake * 70) * 6 * (1 - clamp01(shake / 0.8)) : 0;
    const dimmedDone = state === 'done' && !solid;
    return (_jsxs("div", { style: {
            position: 'absolute',
            left: p.x,
            top: p.y,
            transform: `translate(-50%,-50%) translateX(${shakeX}px)`,
            width,
            height,
            opacity: params.opacity * appear,
            filter: `brightness(${params.brightness})`,
            zIndex: 6,
            pointerEvents: 'none',
        }, children: [_jsx("div", { style: {
                    position: 'absolute',
                    inset: 0,
                    borderRadius: 14,
                    background: BG_ELEVATED,
                    border: `3px solid ${border}`,
                    boxShadow: ring ? `0 0 26px ${YELLOW}66` : state === 'ready' ? `0 0 20px ${GREEN}44` : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: dimmedDone ? 0.72 : 1,
                }, children: _jsx("span", { style: { color: dimmedDone ? CARD_MUTED : CARD_TEXT, fontSize, fontWeight: 900 }, children: state === 'done' ? `✓ ${label}` : label }) }), order != null && state === 'done' && (_jsx("div", { style: {
                    position: 'absolute',
                    left: -14,
                    top: -18,
                    minWidth: 30,
                    height: 30,
                    borderRadius: 15,
                    background: BG_ELEVATED,
                    border: `2px solid ${GREEN}`,
                    color: GREEN,
                    fontFamily: MONO,
                    fontSize: 20,
                    fontWeight: 900,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 4px',
                }, children: order })), badge != null && state !== 'done' && (_jsx("div", { style: {
                    position: 'absolute',
                    left: -16,
                    top: -18,
                    minWidth: 38,
                    height: 38,
                    borderRadius: 19,
                    background: BG_ELEVATED,
                    border: `2px solid ${badge === 0 ? GREEN : RED}`,
                    color: badge === 0 ? GREEN : RED,
                    fontFamily: MONO,
                    fontSize: 24,
                    fontWeight: 900,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 4px',
                }, children: badge }))] }));
}
// Directed edge: a path from a to b with arrowhead and optional travelling pulse.
export function DirectedEdge({ from, to, opacity, color = CYAN, width = 6, pulse, kind = 'curved', waypoints, }) {
    const path = kind === 'follow-link' ? buildPath('follow-link', from, to, { waypoints: waypoints ?? [] }) : buildPath(kind, from, to);
    const samples = path.samples(36);
    const arrow = path.pointAt(0.99);
    const prev = path.pointAt(0.93);
    let dx = arrow.x - prev.x;
    let dy = arrow.y - prev.y;
    const len = Math.hypot(dx, dy) || 1;
    dx /= len;
    dy /= len;
    const dot = pulse ? path.pointAt((((pulse.t + from.x * 0.001) * pulse.speed) % 1 + 1) % 1) : null;
    return (_jsxs("g", { opacity: opacity, children: [_jsx("polyline", { points: samples.map((pt) => `${pt.x},${pt.y}`).join(' '), fill: "none", stroke: color, strokeWidth: width, strokeLinecap: "round" }), _jsx("polygon", { points: `${arrow.x} ${arrow.y} ${arrow.x - 18 * dx - 9 * -dy} ${arrow.y - 18 * dy - 9 * dx} ${arrow.x - 18 * dx + 9 * -dy} ${arrow.y - 18 * dy + 9 * dx}`, fill: color }), dot && _jsx("circle", { cx: dot.x, cy: dot.y, r: 5.5, fill: YELLOW, opacity: 0.95 })] }));
}
// An ordered row of slots that fills left to right (order lanes, tallies).
export function ChipSlots({ order, count, y, label, x, width, height, slotW = 92, slotH = 40, names, }) {
    const recent = order.length - 1;
    return (_jsxs("div", { style: {
            position: 'absolute',
            left: x - width / 2,
            top: y - height / 2,
            width,
            height,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: SURFACE_PANEL,
            border: `2px solid ${GREEN}55`,
            borderRadius: 18,
            padding: '0 16px',
            boxSizing: 'border-box',
        }, children: [_jsx("span", { style: { color: CARD_MUTED, fontSize: 18, fontWeight: 800, letterSpacing: 1, whiteSpace: 'nowrap' }, children: label }), Array.from({ length: count }).map((_, i) => {
                const has = i < order.length;
                const isRecent = has && i === recent;
                const name = has ? names(order[i]) : '·';
                return (_jsx("span", { style: {
                        width: slotW,
                        height: slotH,
                        borderRadius: 10,
                        background: has ? BG_ELEVATED : SURFACE_FAINT,
                        border: `2px solid ${isRecent ? GREEN : has ? BORDER : BORDER_DIM}`,
                        color: has ? GREEN : CARD_MUTED,
                        fontSize: 22,
                        fontWeight: 900,
                        fontFamily: MONO,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: isRecent ? `0 0 16px ${GREEN}44` : 'none',
                    }, children: has ? `${i + 1}.${name}` : '·' }, `slot-${i}`));
            })] }));
}
