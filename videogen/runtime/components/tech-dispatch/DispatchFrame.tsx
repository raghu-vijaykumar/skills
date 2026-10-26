import React from 'react';
import {Img, OffthreadVideo, Sequence} from 'remotion';
import {TECH_DISPATCH as D} from '../../design/techDispatch.ts';

export type DispatchSource = {src: string; kind?: 'image' | 'video'; source: string; label: string; startFrom?: number; sequenceFrom?: number};

// The frame is reusable across source-led reports; the caller supplies its
// topic footer, and restrained chrome keeps the recorded product UI central.
export function DispatchFrame({children, chapter, footer}: {children: React.ReactNode; chapter: string; footer?: string}) {
  return <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: D.stage, color: D.text, fontFamily: D.sans}}>
    <div style={{position: 'absolute', inset: 0, background: `radial-gradient(85% 65% at 50% 27%, ${D.surface} 0%, ${D.stage} 75%)`}} />
    <div style={{position: 'absolute', left: 60, right: 60, top: 42, height: 3, background: D.accent}} />
    <div style={{position: 'absolute', left: 60, top: 62, fontFamily: D.mono, fontSize: 24, fontWeight: 800, letterSpacing: 2, color: D.accent}}>REVISE LABS / TECH DISPATCH</div>
    <div style={{position: 'absolute', right: 60, top: 62, fontFamily: D.mono, fontSize: 24, fontWeight: 700, letterSpacing: 1, color: D.muted}}>{chapter}</div>
    {children}
    {footer ? <div style={{position: 'absolute', left: 60, bottom: 38, fontFamily: D.mono, fontSize: 22, color: D.muted, letterSpacing: 2}}>{footer}</div> : null}
  </div>;
}

export function DispatchHeadline({eyebrow, children}: {eyebrow: string; children: React.ReactNode}) {
  return <div style={{position: 'absolute', left: 74, right: 74, top: 298, zIndex: 10}}>
    <div style={{fontFamily: D.mono, color: D.accent, fontSize: 26, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase'}}>{eyebrow}</div>
    <div style={{fontFamily: D.sans, color: D.text, fontSize: 52, lineHeight: 1.1, fontWeight: 900, letterSpacing: -0.6, marginTop: 12}}>{children}</div>
  </div>;
}

export function EvidencePlate({asset, x, y, w, h, frame = 0, radius = 22}: {asset: DispatchSource; x: number; y: number; w: number; h: number; frame?: number; radius?: number}) {
  return <div style={{position: 'absolute', left: x, top: y, width: w, height: h + 72, background: D.surface, border: `2px solid ${D.rule}`, borderRadius: radius, boxShadow: '0 20px 48px rgba(0,0,0,.4)', overflow: 'hidden'}}>
    <div style={{position: 'relative', width: w, height: h, overflow: 'hidden', background: D.stage}}>
      {asset.kind === 'video' ? <Sequence from={asset.sequenceFrom ?? 0} layout="none"><OffthreadVideo src={asset.src} muted startFrom={asset.startFrom ?? 0} style={{width: w, height: h, objectFit: 'cover'}} /></Sequence> : <Img src={asset.src} style={{width: w, height: h, objectFit: 'cover', transform: `scale(${1 + Math.min(0.06, frame * 0.00008)})`}} />}
    </div>
    <div style={{position: 'absolute', left: 22, right: 22, bottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16}}>
      <span style={{fontSize: 24, fontWeight: 800, whiteSpace: 'nowrap'}}>{asset.label}</span>
      <span style={{fontFamily: D.mono, fontSize: 20, color: D.muted, whiteSpace: 'nowrap'}}>SOURCE: {asset.source}</span>
    </div>
  </div>;
}
