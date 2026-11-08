import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CYAN, TEXT } from '../../design/color.js';
import { FONT_SANS, LINE_HEIGHT, TRACKING, TYPE, WEIGHT } from '../../design/typography.js';
import { BAND } from '../../design/surfaces.js';
// Shared scene title: kicker + one-line title, pinned to the top title band.
// Every short renders this so the 52/26 hierarchy is consistent by construction.
export function Title({ children, kicker }) {
    return (_jsxs("div", { style: { position: 'absolute', top: BAND.titleTop, left: BAND.titleSide, right: BAND.titleSide, fontFamily: FONT_SANS }, children: [kicker && (_jsx("div", { style: {
                    fontSize: TYPE.kicker,
                    letterSpacing: TRACKING.kicker,
                    color: CYAN,
                    fontWeight: WEIGHT.bold,
                    marginBottom: 12,
                }, children: kicker.toUpperCase() })), _jsx("div", { style: { fontSize: TYPE.title, lineHeight: LINE_HEIGHT.title, color: TEXT, fontWeight: WEIGHT.extraBold }, children: children })] }));
}
