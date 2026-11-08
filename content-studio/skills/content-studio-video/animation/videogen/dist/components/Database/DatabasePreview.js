import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Database } from './Database.js';
export const DATABASE_PREVIEW_DURATION_FRAMES = 150;
export const DATABASE_PREVIEW_FPS = 30;
export function DatabasePreview() {
    const frame = useCurrentFrame();
    const t = frame / 30;
    let state = 'idle';
    let trans = undefined;
    let contents = [];
    if (t < 1)
        state = 'idle';
    else if (t < 2) {
        const p = Math.min(1, (t - 1) / 0.8);
        trans = { from: 'idle', to: 'writing', progress: p };
        state = 'writing';
        contents = [{ key: 'pay_8F3A', status: 'writing' }];
    }
    else if (t < 3) {
        state = 'writing';
        contents = [{ key: 'pay_8F3A', status: 'writing' }];
    }
    else {
        state = 'contains-record';
        contents = [
            { key: 'pay_8F3A', value: 'SUCCESS · $100', status: 'ok' },
            { key: 'pay_7F1C', value: 'FAILED', status: 'missing' },
        ];
    }
    return (_jsx(AbsoluteFill, { style: { background: '#05070a', display: 'flex', alignItems: 'center', justifyContent: 'center' }, children: _jsxs("div", { style: { position: 'relative', width: 960, height: 540 }, children: [_jsx("div", { style: { position: 'absolute', left: 330, top: 150 }, children: _jsx(Database, { x: 0, y: 0, name: "PRIMARY DB", label: "MASTER \u00B7 STRONG CONSISTENCY", state: state, transition: trans, contents: contents }) }), _jsx("div", { style: { position: 'absolute', bottom: 40, left: 0, right: 0, textAlign: 'center', color: '#8B949E', fontSize: 13 }, children: "IDLE \u2192 WRITE \u2192 RECORD STORED (responsive contents)" })] }) }));
}
