import {FONT_MONO, FONT_SANS, TYPE} from './typography.ts';
import {BG, BG_ELEVATED, BORDER, BORDER_DIM, CYAN, MUTED, ORANGE, TEXT, YELLOW} from './color.ts';

// Tech Dispatch borrows the house dark foundation. Its editorial layout and
// sourced media provide the distinction, while color and type remain on brand.
export const TECH_DISPATCH = {
  id: 'tech-dispatch',
  stage: BG,
  surface: BG_ELEVATED,
  surfaceAlt: BORDER_DIM,
  text: TEXT,
  muted: MUTED,
  rule: BORDER,
  accent: CYAN,
  response: ORANGE,
  marker: YELLOW,
  onAccent: BG,
  sans: FONT_SANS,
  mono: FONT_MONO,
  type: TYPE,
} as const;
