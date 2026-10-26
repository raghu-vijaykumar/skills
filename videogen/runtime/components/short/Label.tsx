import React from 'react';
import {BG, CYAN, MUTED, SURFACE_CARD} from '../../design/color.ts';
import {FONT_MONO, TRACKING, TYPE, WEIGHT} from '../../design/typography.ts';
import {RADIUS, STROKE} from '../../design/surfaces.ts';

// Shared label system. `Label` is small uppercase tracked text for naming a
// region or value; `Tag` is the bordered chip used for status, counts and
// short values. Both read from the same tokens so labels look identical across
// 2D, 2.5D and 3D scenes.
export function Label({
  children,
  color = MUTED,
  size = TYPE.autocompleteRow,
  style,
}: {
  children: React.ReactNode;
  color?: string;
  size?: number;
  style?: React.CSSProperties;
}) {
  return (
    <span
      style={{
        color,
        fontSize: size,
        fontWeight: WEIGHT.extraBold,
        letterSpacing: TRACKING.label,
        fontFamily: FONT_MONO,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {children}
    </span>
  );
}

export function Tag({
  children,
  tone = CYAN,
  size = TYPE.kicker,
  filled = false,
  style,
}: {
  children: React.ReactNode;
  tone?: string;
  size?: number;
  filled?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <span
      style={{
        display: 'inline-block',
        background: filled ? tone : SURFACE_CARD,
        color: filled ? BG : tone,
        border: `${STROKE.thin}px solid ${tone}`,
        borderRadius: RADIUS.card,
        padding: '6px 16px',
        fontSize: size,
        fontWeight: WEIGHT.black,
        fontFamily: FONT_MONO,
        letterSpacing: TRACKING.label,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {children}
    </span>
  );
}
