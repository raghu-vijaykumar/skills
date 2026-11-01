// Revise Labs house color tokens — the single source of truth for color across
// every video, in every medium.
//
// `src/components/theme.ts` and `src/three/materials.ts` re-export from here so
// the 2D and 3D systems share one foundation. Video sources must select from
// these tokens (or re-export them) instead of hard-coding hex values, so the
// channel keeps one recognizable identity regardless of rendering technique.
//
// Direction (identity pivot, 2026-10): keep the dark cinematic base, but make
// the accents bold and saturated so the channel reads high-energy and
// high-contrast rather than muted. See DESIGN.md "Color".

// Foundation: near-black cinematic background, light readable foreground.
export const BG = '#05070a';
export const BG_ELEVATED = '#0d1117';
export const TEXT = '#f4f8fd';
export const MUTED = '#9aa7b8';
export const BORDER = '#3a4554';
export const BORDER_DIM = '#242d38';

// The canonical accent set. Select from these; never invent a new hue. Values
// are deliberately bold/saturated so a single accent reads as an energy source
// against the dark ground.
export const CYAN = '#00e0ff';
export const GREEN = '#2bff88';
export const RED = '#ff3355';
export const ORANGE = '#ff8a1f';
export const YELLOW = '#ffd400';
export const PURPLE = '#b15cff';
export const MAGENTA = '#ff2e93';

// Semantic aliases so meaning survives when an accent is remapped.
export const SUCCESS = GREEN;
export const WARNING = YELLOW;
export const DANGER = RED;
export const INFO = CYAN;

// Glow tints — the lighter, translucent form of each accent for shadows, halos
// and highlights. Use these for `box-shadow`/glow so energy reads as light, not
// as a flat fill.
export const ACCENT_GLOW = {
  cyan: 'rgba(0,224,255,0.55)',
  green: 'rgba(43,255,136,0.5)',
  red: 'rgba(255,51,85,0.55)',
  orange: 'rgba(255,138,31,0.55)',
  yellow: 'rgba(255,212,0,0.5)',
  purple: 'rgba(177,92,255,0.55)',
  magenta: 'rgba(255,46,147,0.55)',
} as const;

// Gradient ramps (accent -> hot tint) for energy surfaces and eye-catching
// fills. Ordered dark/deep -> light/hot so `linear-gradient(135deg, …)` reads
// as a lit surface rather than a flat swatch.
export const ACCENT_GRADIENT = {
  cyan: ['#005c78', CYAN, '#9df3ff'],
  green: ['#0b6b3a', GREEN, '#c3ffdd'],
  red: ['#8a1230', RED, '#ff9db0'],
  orange: ['#8a3c00', ORANGE, '#ffd0a3'],
  yellow: ['#8a6d00', YELLOW, '#fff2a8'],
  purple: ['#4a1e8a', PURPLE, '#dcc3ff'],
  magenta: ['#8a1050', MAGENTA, '#ffc4e0'],
} as const;

// Translucent surfaces used by cards, panels, queues, code blocks and pills.
export const SURFACE_CARD = 'rgba(13,17,23,0.92)';
export const SURFACE_PANEL = 'rgba(13,17,23,0.55)';
export const SURFACE_CODE = 'rgba(13,17,23,0.6)';
export const SURFACE_PILL = 'rgba(13,17,23,0.9)';
export const SURFACE_FAINT = 'rgba(13,17,23,0.5)';

export const COLOR = {
  bg: BG,
  bgElevated: BG_ELEVATED,
  text: TEXT,
  muted: MUTED,
  border: BORDER,
  borderDim: BORDER_DIM,
  accent: {cyan: CYAN, green: GREEN, red: RED, orange: ORANGE, yellow: YELLOW, purple: PURPLE, magenta: MAGENTA},
  semantic: {success: SUCCESS, warning: WARNING, danger: DANGER, info: INFO},
  surface: {card: SURFACE_CARD, panel: SURFACE_PANEL, code: SURFACE_CODE, pill: SURFACE_PILL, faint: SURFACE_FAINT},
  glow: ACCENT_GLOW,
  gradient: ACCENT_GRADIENT,
} as const;
