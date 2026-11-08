import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Img, OffthreadVideo, Sequence } from 'remotion';
import { EVIDENCE_LAB as E } from '../../design/evidenceLab.js';
// The frame is intentionally spare so recorded work, not decorative chrome,
// remains the focal subject. The caption band above the content stays free.
export function EvidenceLabFrame({ children, phase }) {
    return _jsxs("div", { style: { position: 'absolute', inset: 0, overflow: 'hidden', background: E.stage, color: E.text, fontFamily: E.sans }, children: [_jsx("div", { style: { position: 'absolute', top: 42, left: 60, right: 60, height: 3, background: E.method } }), _jsx("div", { style: { position: 'absolute', top: 62, left: 60, fontFamily: E.mono, fontSize: E.type.autocompleteRow, fontWeight: 800, letterSpacing: 2, color: E.method }, children: "REVISE LABS / EVIDENCE LAB" }), _jsx("div", { style: { position: 'absolute', top: 62, right: 60, fontFamily: E.mono, fontSize: E.type.autocompleteRow, fontWeight: 700, letterSpacing: 2, color: E.muted }, children: phase }), children] });
}
// Keep every original pixel in view. Detail crops or highlights belong in
// separate, explicitly labeled shots rather than silently altering evidence.
export function EvidenceCapture({ asset, x, y, width, height }) {
    if (!asset.meta.evidence?.capturedAt || !asset.meta.evidence.method)
        throw new Error(`EvidenceCapture ${asset.meta.id} lacks capture provenance`);
    return _jsxs("div", { style: { position: 'absolute', left: x, top: y, width, height, border: `2px solid ${E.rule}`, borderRadius: 18, background: E.surface, overflow: 'hidden' }, children: [_jsx("div", { style: { position: 'absolute', inset: '0 0 124px 0', background: E.stage, display: 'flex', alignItems: 'center', justifyContent: 'center' }, children: asset.kind === 'video'
                    ? _jsx(Sequence, { from: asset.sequenceFrom ?? 0, layout: "none", children: _jsx(OffthreadVideo, { src: asset.src, muted: true, startFrom: asset.startFrom ?? 0, style: { width: '100%', height: '100%', objectFit: 'contain' } }) })
                    : _jsx(Img, { src: asset.src, style: { width: '100%', height: '100%', objectFit: 'contain' } }) }), _jsxs("div", { style: { position: 'absolute', left: 22, right: 22, bottom: 18, display: 'grid', gap: 6, fontFamily: E.mono, fontSize: E.type.autocompleteRow, color: E.muted }, children: [_jsxs("div", { style: { color: E.text, fontWeight: 800 }, children: ["CAPTURE ", asset.meta.id, " \u00B7 ", asset.meta.evidence.capturedAt] }), _jsxs("div", { children: [asset.meta.attribution ?? 'Revise Labs capture', " \u00B7 ", asset.meta.evidence.method] })] })] });
}
export function EvidenceFinding({ kind, children, x, y, width }) {
    const color = kind === 'observed' ? E.observed : kind === 'contradicted' ? E.contradicted : kind === 'limitation' ? E.limitation : E.method;
    return _jsxs("div", { style: { position: 'absolute', left: x, top: y, width, borderLeft: `5px solid ${color}`, paddingLeft: 22 }, children: [_jsx("div", { style: { fontFamily: E.mono, fontSize: E.type.kicker, fontWeight: 800, letterSpacing: 2, color, textTransform: 'uppercase' }, children: kind }), _jsx("div", { style: { fontSize: E.type.callout, lineHeight: 1.3, fontWeight: 700, marginTop: 10 }, children: children })] });
}
