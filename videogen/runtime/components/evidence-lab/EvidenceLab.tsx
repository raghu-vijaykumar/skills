import React from 'react';
import {Img, OffthreadVideo, Sequence} from 'remotion';
import {EVIDENCE_LAB as E} from '../../design/evidenceLab.ts';

export type CapturedEvidence = {
  src: string;
  kind: 'image' | 'video';
  // Pass a record from the generated SOURCE_ASSET_META; provenance should not
  // be retyped into a scene and allowed to drift from the committed manifest.
  meta: {id: string; attribution?: string | null; evidence?: {capturedAt?: string; method?: string} | null};
  startFrom?: number;
  sequenceFrom?: number;
};

// The frame is intentionally spare so recorded work, not decorative chrome,
// remains the focal subject. The caption band above the content stays free.
export function EvidenceLabFrame({children, phase}: {children: React.ReactNode; phase: 'QUESTION' | 'METHOD' | 'RUN' | 'FINDING' | 'LIMIT'}) {
  return <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: E.stage, color: E.text, fontFamily: E.sans}}>
    <div style={{position: 'absolute', top: 42, left: 60, right: 60, height: 3, background: E.method}} />
    <div style={{position: 'absolute', top: 62, left: 60, fontFamily: E.mono, fontSize: E.type.autocompleteRow, fontWeight: 800, letterSpacing: 2, color: E.method}}>REVISE LABS / EVIDENCE LAB</div>
    <div style={{position: 'absolute', top: 62, right: 60, fontFamily: E.mono, fontSize: E.type.autocompleteRow, fontWeight: 700, letterSpacing: 2, color: E.muted}}>{phase}</div>
    {children}
  </div>;
}

// Keep every original pixel in view. Detail crops or highlights belong in
// separate, explicitly labeled shots rather than silently altering evidence.
export function EvidenceCapture({asset, x, y, width, height}: {asset: CapturedEvidence; x: number; y: number; width: number; height: number}) {
  if (!asset.meta.evidence?.capturedAt || !asset.meta.evidence.method) throw new Error(`EvidenceCapture ${asset.meta.id} lacks capture provenance`);
  return <div style={{position: 'absolute', left: x, top: y, width, height, border: `2px solid ${E.rule}`, borderRadius: 18, background: E.surface, overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: '0 0 124px 0', background: E.stage, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      {asset.kind === 'video'
        ? <Sequence from={asset.sequenceFrom ?? 0} layout="none"><OffthreadVideo src={asset.src} muted startFrom={asset.startFrom ?? 0} style={{width: '100%', height: '100%', objectFit: 'contain'}} /></Sequence>
        : <Img src={asset.src} style={{width: '100%', height: '100%', objectFit: 'contain'}} />}
    </div>
    <div style={{position: 'absolute', left: 22, right: 22, bottom: 18, display: 'grid', gap: 6, fontFamily: E.mono, fontSize: E.type.autocompleteRow, color: E.muted}}>
      <div style={{color: E.text, fontWeight: 800}}>CAPTURE {asset.meta.id} · {asset.meta.evidence.capturedAt}</div>
      <div>{asset.meta.attribution ?? 'Revise Labs capture'} · {asset.meta.evidence.method}</div>
    </div>
  </div>;
}

export function EvidenceFinding({kind, children, x, y, width}: {kind: 'observed' | 'inference' | 'limitation' | 'contradicted'; children: React.ReactNode; x: number; y: number; width: number}) {
  const color = kind === 'observed' ? E.observed : kind === 'contradicted' ? E.contradicted : kind === 'limitation' ? E.limitation : E.method;
  return <div style={{position: 'absolute', left: x, top: y, width, borderLeft: `5px solid ${color}`, paddingLeft: 22}}>
    <div style={{fontFamily: E.mono, fontSize: E.type.kicker, fontWeight: 800, letterSpacing: 2, color, textTransform: 'uppercase'}}>{kind}</div>
    <div style={{fontSize: E.type.callout, lineHeight: 1.3, fontWeight: 700, marginTop: 10}}>{children}</div>
  </div>;
}
