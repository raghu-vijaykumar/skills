import {FONT_MONO, FONT_SANS, TYPE} from './typography.ts';
import {BG, BG_ELEVATED, BORDER, CYAN, GREEN, MUTED, RED, TEXT, YELLOW} from './color.ts';

// Evidence Lab uses the house palette; method, observation, and uncertainty
// change the editorial grammar without creating a new brand identity.
export const EVIDENCE_LAB = {
  id: 'evidence-lab',
  stage: BG,
  surface: BG_ELEVATED,
  text: TEXT,
  muted: MUTED,
  rule: BORDER,
  method: CYAN,
  observed: GREEN,
  limitation: YELLOW,
  contradicted: RED,
  sans: FONT_SANS,
  mono: FONT_MONO,
  type: TYPE,
} as const;
