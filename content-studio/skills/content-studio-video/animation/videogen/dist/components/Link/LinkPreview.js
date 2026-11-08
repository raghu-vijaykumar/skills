import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Link } from './Link.js';
export const LINK_PREVIEW_DURATION_FRAMES = 150;
export const LINK_PREVIEW_FPS = 30;
const STATES = [
    { state: 'active', label: 'ACTIVE' },
    { state: 'success', label: 'SUCCESS' },
    { state: 'failed', label: 'FAILED' },
    { state: 'disconnected', label: 'DISCONNECTED' },
];
export function LinkPreview() {
    const frame = useCurrentFrame();
    const t = frame / 30;
    const phase = Math.min(STATES.length - 1, Math.floor(t / 1.2));
    return (_jsx(AbsoluteFill, { style: { background: '#05070a', display: 'flex', alignItems: 'center', justifyContent: 'center' }, children: _jsxs("div", { style: { position: 'relative', width: 960, height: 540 }, children: [STATES.map((item, i) => {
                    const show = i <= phase;
                    const y = 60 + i * 92;
                    return (_jsxs("div", { style: { position: 'absolute', left: 60, top: y, width: 840, opacity: show ? 1 : 0 }, children: [_jsx("div", { style: { position: 'absolute', left: 0, top: 34, width: 120, fontSize: 11, fontWeight: 800, letterSpacing: 1, color: '#8B949E' }, children: item.label }), _jsx(Link, { x: 180, y: 30, width: 520, state: item.state, direction: item.state === 'active' ? 'both' : item.state === 'failed' || item.state === 'disconnected' ? 'right' : 'right', label: item.state === 'disconnected' ? 'connection lost' : item.state === 'failed' ? 'request' : 'payment' })] }, item.state));
                }), _jsx("div", { style: { position: 'absolute', bottom: 30, left: 0, right: 0, textAlign: 'center', color: '#8B949E', fontSize: 12 }, children: "Link \u2014 states: active / success / failed / disconnected" })] }) }));
}
