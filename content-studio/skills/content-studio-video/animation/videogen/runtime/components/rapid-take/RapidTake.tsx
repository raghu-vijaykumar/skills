import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {RAPID_TAKE as R} from '../../design/rapidTake.ts';

// Reusable primitives for the Rapid Take video style. They deliberately do one
// thing each: a shot, a slam, a source mark, a reaction, an annotation. The
// draft composes them on a 2–5 second beat grid instead of inventing a new
// screen grammar per scene.

export function RapidStage({children, grid = false}: {children: React.ReactNode; grid?: boolean}) {
  return <AbsoluteFill style={{background: R.stage, color: R.text, fontFamily: R.sans, overflow: 'hidden'}}>
    {grid ? <div style={{position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: `linear-gradient(${R.rule} 1px, transparent 1px), linear-gradient(90deg, ${R.rule} 1px, transparent 1px)`, backgroundSize: '96px 96px'}} /> : null}
    {children}
  </AbsoluteFill>;
}

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export function Slam({lines, color = R.text, size = 150, align = 'left', top = 0.24, delay = 0, accent}: {lines: string[]; color?: string; size?: number; align?: 'left' | 'center'; top?: number; delay?: number; accent?: number}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <div style={{position: 'absolute', left: align === 'center' ? 90 : 110, right: 90, top: `${top * 100}%`, display: 'flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : 'flex-start', textAlign: align}}>
    {lines.map((line, index) => {
      const at = delay + index * 0.09;
      const progress = interpolate(frame / fps, [at, at + 0.18], [0, 1], clamp);
      return <div key={`${line}-${index}`} style={{fontSize: size, lineHeight: 0.94, fontWeight: 900, letterSpacing: '-0.055em', textTransform: 'uppercase', color: index === accent ? R.hot : color, opacity: progress, transform: `translateY(${(1 - progress) * 36}px) scale(${0.92 + progress * 0.08})`, textShadow: index === accent ? `0 0 70px ${R.hot}55` : 'none'}}>{line}</div>;
    })}
  </div>;
}

export function StatSlam({value, label, color = R.zap, size = 300, top = 0.2}: {value: string; label: string; color?: string; size?: number; top?: number}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = interpolate(frame / fps, [0, 0.07, 0.24], [1.3, 0.96, 1], clamp);
  return <div style={{position: 'absolute', left: 80, right: 80, top: `${top * 100}%`, textAlign: 'center'}}>
    <div style={{fontSize: size, lineHeight: 0.82, fontWeight: 900, letterSpacing: '-0.07em', color, transform: `scale(${pop})`, textShadow: `0 0 90px ${color}66`}}>{value}</div>
    <div style={{fontFamily: R.mono, fontSize: 40, letterSpacing: 3, marginTop: 24, color: R.text, textTransform: 'uppercase'}}>{label}</div>
  </div>;
}

export function SourceShot({src, kind = 'image', source, label, startFrom = 0, zoom = 1.05, position = 'center', dim = 0.18, fit = 'cover', children}: {src: string; kind?: 'image' | 'video'; source: string; label?: string; startFrom?: number; zoom?: number; position?: string; dim?: number; fit?: 'cover' | 'contain'; children?: React.ReactNode}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const scale = interpolate(frame / fps, [0, 6], [1, zoom], clamp);
  const media = kind === 'video'
    ? <OffthreadVideo src={src} muted startFrom={startFrom} style={{width: '100%', height: '100%', objectFit: fit, objectPosition: position, transform: `scale(${scale})`}} />
    : <Img src={src} style={{width: '100%', height: '100%', objectFit: fit, objectPosition: position, transform: `scale(${scale})`}} />;
  return <div style={{position: 'absolute', inset: 0, background: R.stage}}>
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>{media}</div>
    <div style={{position: 'absolute', inset: 0, background: `linear-gradient(180deg, rgba(5,5,5,.18) 0%, transparent 32%, rgba(5,5,5,${dim}) 100%)`}} />
    {children}
    <div style={{position: 'absolute', left: 30, bottom: 26, display: 'flex', gap: 14, alignItems: 'center', fontFamily: R.mono, fontSize: 24, letterSpacing: 1.5, color: R.text, textShadow: '0 2px 10px #000'}}>
      <span style={{background: R.hot, color: R.onHot, padding: '4px 10px', fontWeight: 800}}>SOURCE</span>
      <span>{label ? `${label} · ${source}` : source}</span>
    </div>
  </div>;
}

export function BrowserFrame({src, url, x = 90, y = 90, w = 1740, h = 900, dark = false}: {src: string; url: string; x?: number; y?: number; w?: number; h?: number; dark?: boolean}) {
  return <div style={{position: 'absolute', left: x, top: y, width: w, height: h, background: dark ? '#16181d' : '#f4f4f2', border: `2px solid ${R.rule}`, boxShadow: '0 30px 90px rgba(0,0,0,.65)', overflow: 'hidden'}}>
    <div style={{height: 42, display: 'flex', alignItems: 'center', gap: 9, padding: '0 16px', background: dark ? '#22252b' : '#dddcd7', borderBottom: `1px solid ${dark ? '#33373f' : '#c9c8c2'}`}}>
      {['#ff5f57', '#febc2e', '#28c840'].map((color) => <span key={color} style={{width: 11, height: 11, borderRadius: 99, background: color}} />)}
      <div style={{flex: 1, marginLeft: 16, fontFamily: R.mono, fontSize: 17, color: dark ? R.muted : '#555', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{url}</div>
    </div>
    <Img src={src} style={{width: '100%', height: `calc(100% - 42px)`, objectFit: 'cover', objectPosition: 'top'}} />
  </div>;
}

export function MemeCut({src, label, startFrom = 0, fit = 'cover'}: {src: string; label: string; startFrom?: number; fit?: 'cover' | 'contain'}) {
  return <AbsoluteFill style={{background: R.stage, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      <OffthreadVideo src={src} muted startFrom={startFrom} style={{width: '100%', height: '100%', objectFit: fit}} />
    </div>
    <div style={{position: 'absolute', top: 34, left: 34, background: R.stage, color: R.zap, border: `2px solid ${R.zap}`, padding: '8px 14px', fontFamily: R.mono, fontSize: 24, letterSpacing: 2}}>REACTION · NOT EVIDENCE</div>
    <div style={{position: 'absolute', bottom: 54, left: 60, right: 60, textAlign: 'center', fontFamily: R.sans, fontSize: 72, fontWeight: 900, letterSpacing: '-0.03em', textTransform: 'uppercase', textShadow: '0 6px 34px #000'}}>{label}</div>
  </AbsoluteFill>;
}

export type AnnotationKind = 'box' | 'circle' | 'arrow' | 'underline';

export function Annotation({kind, x, y, w, h, label, color = R.zap, delay = 0, to}: {kind: AnnotationKind; x: number; y: number; w: number; h: number; label?: string; color?: string; delay?: number; to?: [number, number]}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame / fps, [delay, delay + 0.28], [0, 1], clamp);
  if (kind === 'box') return <div style={{position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, border: `7px solid ${color}`, boxShadow: `0 0 24px ${color}66`, clipPath: `inset(0 ${100 - p * 100}% 0 0)`}}>
    {label ? <div style={{position: 'absolute', left: -7, top: -52, background: color, color: R.stage, fontFamily: R.mono, fontSize: 26, fontWeight: 900, letterSpacing: 1, padding: '4px 10px', whiteSpace: 'nowrap'}}>{label}</div> : null}
  </div>;
  if (kind === 'underline') return <div style={{position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w * p}%`, height: `${h}%`, background: color, transform: 'skewX(-8deg)', transformOrigin: 'left'}} />;
  if (kind === 'circle') return <svg style={{position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, overflow: 'visible'}} viewBox="0 0 100 100" preserveAspectRatio="none">
    <ellipse cx="50" cy="50" rx="46" ry="44" fill="none" stroke={color} strokeWidth="3.4" strokeLinecap="round" strokeDasharray="320" strokeDashoffset={320 * (1 - p)} />
    {label ? <text x="4" y="8" fill={color} fontFamily={R.mono} fontSize="5.2" fontWeight="800">{label}</text> : null}
  </svg>;
  const target = to ?? [x + w, y + h];
  const dx = target[0] - x;
  const dy = target[1] - y;
  const angle = Math.atan2(dy, dx) * 180 / Math.PI;
  const length = Math.sqrt(dx * dx + dy * dy);
  return <svg style={{position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', overflow: 'visible'}} viewBox="0 0 100 100" preserveAspectRatio="none">
    <line x1={x} y1={y} x2={x + dx * p} y2={y + dy * p} stroke={color} strokeWidth="1.1" strokeLinecap="round" />
    {p > 0.9 ? <g transform={`translate(${target[0]} ${target[1]}) rotate(${angle})`}><polygon points="0,0 -2.6,-1.4 -2.6,1.4" fill={color} /></g> : null}
    {label ? <text x={x + dx * 0.45} y={y + dy * 0.45 - 1.4} fill={color} fontFamily={R.mono} fontSize="4.4" fontWeight="800">{label}</text> : null}
    <title>{`arrow ${length.toFixed(0)}`}</title>
  </svg>;
}

export function LowerThird({left, right, color = R.text}: {left: string; right?: string; color?: string}) {
  return <div style={{position: 'absolute', left: 34, right: 34, bottom: 22, display: 'flex', justifyContent: 'space-between', borderTop: `2px solid ${R.rule}`, paddingTop: 10, fontFamily: R.mono, fontSize: 22, letterSpacing: 1.5, color}}>
    <span>{left}</span>{right ? <span style={{color: R.muted}}>{right}</span> : null}
  </div>;
}

export function CutFlash({color = '#ffffff'}: {color?: string}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(frame / fps, [0, 0.045], [0.9, 0], clamp);
  return <AbsoluteFill style={{background: color, opacity, zIndex: 90, pointerEvents: 'none'}} />;
}
