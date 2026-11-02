import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {MUTED, TEXT} from '../../design/color.ts';
import {FONT_SANS, LINE_HEIGHT, TYPE, WEIGHT} from '../../design/typography.ts';
import {BAND} from '../../design/surfaces.ts';

// Shared caption bar, shown below the title in the reserved caption band so it
// never collides with the visual. Displays the current narration phrase
// word-by-word, driven by generated cue timing.
export function Captions({
  cues,
  y = BAND.captionY,
  fontSize = TYPE.caption,
}: {
  cues: readonly {id: string; text: string; startSeconds: number; endSeconds: number}[];
  y?: number;
  fontSize?: number;
}) {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const t = frame / fps;

  const active = cues.find((c) => t >= c.startSeconds && t < c.endSeconds);
  if (!active) return null;

  const progress = Math.max(0, Math.min(1, (t - active.startSeconds) / Math.max(0.001, active.endSeconds - active.startSeconds)));
  const words = active.text.split(/\s+/);
  const spoken = Math.floor(progress * words.length);

  return (
    <div
      data-captions
      style={{
        position: 'absolute',
        left: '50%',
        top: y * height,
        transform: 'translateX(-50%)',
        width: '86%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '0 8px',
        textAlign: 'center',
        lineHeight: LINE_HEIGHT.caption,
        pointerEvents: 'none',
        fontFamily: FONT_SANS,
      }}
    >
      {words.map((word, i) => {
        const done = i < spoken;
        const isCurrent = i === spoken;
        return (
          <span
            key={i}
            style={{
              fontSize,
              fontWeight: WEIGHT.extraBold,
              color: isCurrent ? TEXT : done ? TEXT : MUTED,
              opacity: isCurrent ? 1 : done ? 0.92 : 0.55,
              background: isCurrent ? 'rgba(13,17,23,0.9)' : 'transparent',
              padding: isCurrent ? '2px 6px' : 0,
              borderRadius: 6,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
}
