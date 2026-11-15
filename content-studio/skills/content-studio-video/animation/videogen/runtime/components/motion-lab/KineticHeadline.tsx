import React from 'react';
import {CYAN, MUTED, TEXT} from '../../design/color.ts';

export type HeadlinePart = {text: string; emphasis?: boolean; strong?: boolean};
export type HeadlineCue = {
  start: number;
  end: number;
  lines: readonly (readonly HeadlinePart[])[];
};

export type KineticHeadlineProps = {
  now: number;
  cues: readonly HeadlineCue[];
  color?: string;
  muted?: string;
  accent?: string;
  fontSize?: number;
  width?: number;
  top?: number;
  selectionHandles?: boolean;
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

// A cue owns its entire time range, so the headline never depends on render order.
export const activeHeadlineCue = (cues: readonly HeadlineCue[], now: number): HeadlineCue | undefined => {
  for (let index = cues.length - 1; index >= 0; index--) {
    if (now >= cues[index].start && now < cues[index].end) return cues[index];
  }
  return undefined;
};

export function KineticHeadline({
  now,
  cues,
  color = TEXT,
  muted = MUTED,
  accent = CYAN,
  fontSize = 54,
  width = 960,
  top = 315,
  selectionHandles = false,
}: KineticHeadlineProps) {
  const cue = activeHeadlineCue(cues, now);
  if (!cue) return null;
  // A short cue lead keeps a newly spoken word visible on its boundary frame.
  const reveal = clamp01((now - cue.start + 0.2) / 0.2);
  const exit = clamp01((cue.end - now + 0.1) / 0.1);
  const opacity = Math.min(reveal, exit);
  return (
    <div style={{position: 'absolute', top, left: '50%', width, transform: `translate(-50%, ${(1 - reveal) * 18}px)`, textAlign: 'center', fontFamily: 'Arial, Helvetica, sans-serif', fontSize, fontWeight: 600, lineHeight: 1.18, opacity, zIndex: 20}}>
      {cue.lines.map((line, lineIndex) => (
        <div key={lineIndex} style={{minHeight: fontSize * 1.2}}>
          {line.map((part, partIndex) => (
            <span key={partIndex} style={{position: 'relative', color: part.emphasis || part.strong ? color : muted, fontWeight: part.emphasis || part.strong ? 800 : 500, outline: part.emphasis ? `2px solid ${accent}` : undefined, outlineOffset: part.emphasis ? 2 : undefined, whiteSpace: 'pre'}}>
              {part.text}
              {part.emphasis && selectionHandles && <><span style={{position: 'absolute', left: -8, top: -10, width: 12, height: 12, borderRadius: '50%', background: accent}}/><span style={{position: 'absolute', right: -8, bottom: -10, width: 12, height: 12, borderRadius: '50%', background: accent}}/></>}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}
