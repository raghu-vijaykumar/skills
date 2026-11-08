import { jsx as _jsx } from "react/jsx-runtime";
import { FONT_SANS } from '../../design/typography.js';
// Shared scene shell: applies the house font and clips overflow. The background
// stays transparent so the composition's own background shows through.
export function SceneFrame({ children, background = 'transparent' }) {
    return (_jsx("div", { style: { position: 'absolute', inset: 0, background, fontFamily: FONT_SANS, overflow: 'hidden' }, children: children }));
}
