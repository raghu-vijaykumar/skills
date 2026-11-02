import React from 'react';
import {ease} from '../../animation/easing.ts';
import {emphasisParams} from '../../animation/attention.ts';
import {CYAN, MUTED, SURFACE_PILL, TEXT} from '../../design/color.ts';
import {FONT_MONO} from '../../design/typography.ts';

const MONO = FONT_MONO;

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export type TextTiming = {start: number; end: number};

// Resolve a span's eased progress from `now` (deterministic, cue-derived).
export const spanProgress = (now: number, timing: TextTiming) =>
  clamp01((now - timing.start) / Math.max(0.001, timing.end - timing.start));

// Word-by-word reveal driven by generated narration timing. Spoken words light
// up as the cue advances; the current word is emphasised.
export function WordReveal({
  text,
  now,
  start,
  end,
  fontSize = 40,
  color = TEXT,
  muted = MUTED,
  accent,
  lineHeight = 1.3,
}: {
  text: string;
  now: number;
  start: number;
  end: number;
  fontSize?: number;
  color?: string;
  muted?: string;
  accent?: string;
  lineHeight?: number;
}) {
  const words = text.split(/\s+/);
  const spoken = Math.min(words.length, Math.max(0, Math.floor(spanProgress(now, {start, end}) * words.length)));
  return (
    <span style={{lineHeight}}>
      {words.map((word, index) => {
        const done = index < spoken;
        const current = index === spoken;
        return (
          <span
            key={`${word}-${index}`}
            style={{
              fontSize,
              fontWeight: 800,
              color: current && accent ? accent : done || current ? color : muted,
              opacity: done || current ? 1 : 0.45,
              background: current ? SURFACE_PILL : 'transparent',
              padding: current ? '2px 6px' : 0,
              borderRadius: 6,
            }}
          >
            {word}{' '}
          </span>
        );
      })}
    </span>
  );
}

export function PhraseReveal({
  children,
  now,
  start,
  duration = 0.5,
  rise = 12,
}: {
  children: React.ReactNode;
  now: number;
  start: number;
  duration?: number;
  rise?: number;
}) {
  const p = clamp01((now - start) / Math.max(0.001, duration));
  return (
    <span style={{display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * rise}px)`}}>{children}</span>
  );
}

// Emphasis applied from an attention level (primary/secondary/background).
export function Emphasis({
  children,
  level,
  glowColor,
  style,
}: {
  children: React.ReactNode;
  level: 'primary' | 'secondary' | 'background';
  glowColor: string;
  style?: React.CSSProperties;
}) {
  const params = emphasisParams(level);
  const glow = params.glow > 0 ? `0 0 ${Math.round(26 * params.glow)}px ${glowColor}66` : undefined;
  return (
    <span
      style={{
        ...style,
        display: 'inline-block',
        opacity: params.opacity,
        filter: `brightness(${params.brightness})`,
        textShadow: glow,
      }}
    >
      {children}
    </span>
  );
}

// Counter that eases 0 -> value inside [start, end]; value changes are smooth.
export function CountUp({
  value,
  now,
  start,
  duration = 0.6,
  easing = 'easeOut',
  style,
}: {
  value: number;
  now: number;
  start: number;
  duration?: number;
  easing?: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'backOut';
  style?: React.CSSProperties;
}) {
  const p = clamp01((now - start) / Math.max(0.001, duration));
  const shown = Math.round(value * ease(p, easing));
  return <span style={{...style, fontFamily: MONO}}>{shown}</span>;
}

// Line-by-line code highlight. `activeLine` (or derived from `start` + step)
// drives which line is emphasised. Indentation is preserved verbatim.
export function CodeHighlight({
  lines,
  activeLine,
  now,
  start = 0,
  step = 0.4,
  fontSize = 20,
  activeColor = CYAN,
  muted = MUTED,
  textColor = TEXT,
  lineHeight = 1.45,
}: {
  lines: string[];
  activeLine?: number;
  now?: number;
  start?: number;
  step?: number;
  fontSize?: number;
  activeColor?: string;
  muted?: string;
  textColor?: string;
  lineHeight?: number;
}) {
  const derived = now != null && start != null ? Math.min(lines.length - 1, Math.floor(((now as number) - start) / (step ?? 0.4))) : 0;
  const active = activeLine ?? Math.max(0, derived);
  return (
    <div style={{whiteSpace: 'pre', fontSize, fontWeight: 900, lineHeight, fontFamily: MONO}}>
      {lines.map((line, index) => {
        const isActive = index === active;
        return (
          <div
            key={`${index}`}
            style={{
              color: isActive ? activeColor : textColor,
              opacity: isActive ? 1 : 0.6,
              background: isActive ? `${activeColor}18` : 'transparent',
              borderRadius: 4,
              padding: '0 8px',
              width: 'fit-content',
            }}
          >
            {line}
          </div>
        );
      })}
    </div>
  );
}

export {MONO};
