// Revise Labs surface tokens — the shapes, strokes, spacing and opacities that
// keep cards, labels, panels and the caption band consistent across videos.

export const RADIUS = {
  sm: 6,
  slot: 10,
  card: 14,
  panel: 16,
  queue: 18,
  board: 22,
  pill: 999,
} as const;

export const STROKE = {
  hairline: 1,
  thin: 2,
  frame: 3,
} as const;

export const OPACITY = {
  muted: 0.55,
  done: 0.92,
  watermark: 0.55,
  glow: 0.85,
} as const;

// Reserved composition bands (fractions of the 9:16 canvas unless noted).
export const BAND = {
  captionY: 0.115,
  titleTop: 56,
  titleSide: 72,
  contentPadding: 48,
} as const;
