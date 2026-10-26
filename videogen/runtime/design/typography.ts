// Revise Labs typography tokens — one font system and one predictable hierarchy
// for every video. The `TYPE` scale is the machine-enforced "Short typography"
// table in DESIGN.md; `scripts/check-short-style.mts` validates these values.

// Font stacks. `FONT_SANS` for prose/titles, `FONT_MONO` for values, code and
// identifiers. Never introduce a third family.
export const FONT_SANS = "'Inter', 'Segoe UI', Arial, sans-serif";
export const FONT_MONO = "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace";

// The canonical type scale (px at 1080px portrait width).
export const TYPE = {
  title: 52,
  kicker: 26,
  caption: 40,
  chip: 32,
  callout: 30,
  listRow: 28,
  bigO: 38,
  inlineComplexity: 34,
  search: 34,
  resultBadge: 26,
  autocompleteRow: 24,
} as const;

export const WEIGHT = {
  regular: 400,
  medium: 500,
  bold: 700,
  extraBold: 800,
  black: 900,
} as const;

export const TRACKING = {
  kicker: 4,
  label: 2,
  tight: -0.5,
} as const;

export const LINE_HEIGHT = {
  title: 1.1,
  caption: 1.4,
  body: 1.3,
  code: 1.45,
} as const;

export const TYPE_SCALE = TYPE;
