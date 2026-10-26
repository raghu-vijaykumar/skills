// Shared 3D material + color tokens for Revise Labs 3D videos.
//
// Visual language: dark cinematic background + LIGHT matte/satin objects with
// realistic material-specific colors and restrained accents. Objects should
// separate from the background by being lighter than it, not by being glossy.
// Keep the palette cohesive across every future 3D video.
//
// The foundation colors (bg/text/muted) come from the shared design system so
// 2D and 3D share one identity. The 3D-only material palette stays here.

import {BG, MUTED, TEXT} from '../design/color.ts';

export type StandardMat = {
  color: string;
  roughness: number;
  metalness: number;
  emissive?: string;
  emissiveIntensity?: number;
  transparent?: boolean;
  opacity?: number;
  toneMapped?: boolean;
};

export const PALETTE = {
  // foundation (shared with the 2D design system)
  bg: BG,
  bgDeep: '#02040a',
  text: TEXT,
  muted: MUTED,

  // light neutral plastics (primary objects)
  plasticLight: '#e6ebf2',
  plasticMid: '#ccd5e0',
  plasticShade: '#aab6c4',

  // glass / fiber (translucent light)
  glassCore: '#d9f3ff',
  glassCoreHi: '#eefaff',
  glassClad: '#a9cdf0',
  glassCladDeep: '#7fb0dd',

  // metals
  metalLight: '#cfd8e3',
  metalDark: '#8f9aa8',
  copper: '#b87333',

  // natural
  wood: '#c9a26b',

  // cable jacket / rubber
  rubber: '#b5764e',
  rubberDark: '#7a4c33',

  // pale teaching glass core (visible, not invisible)
  coreWhite: '#eef3f7',

  // subsea environment (kept dark so light objects separate)
  seaDeep: '#040910',
  seabed: '#2b3646',
  rock: '#8b97a6',
  seaLight: '#a9d4ff',

  // bold semantic accents (light / data / energy / signal / detect / pop),
  // aligned with the saturated accent set in src/design/color.ts
  accentLight: '#fff3b0',
  accentLightHot: '#fffbe6',
  accentData: '#00e0ff',
  accentEnergy: '#b15cff',
  accentSignal: '#ffd400',
  accentDetect: '#2bff88',
  accentWarn: '#ff8a1f',
  accentPop: '#ff2e93',
} as const;

export const MAT = {
  /** Light neutral matte plastic — the default for primary objects. */
  plastic: {color: PALETTE.plasticLight, roughness: 0.68, metalness: 0} as StandardMat,
  /** Slightly darker satin plastic for secondary shells / jackets. */
  satin: {color: PALETTE.plasticMid, roughness: 0.46, metalness: 0.08} as StandardMat,
  /** Light satin metal (not mirrored). */
  metal: {color: PALETTE.metalLight, roughness: 0.34, metalness: 0.85} as StandardMat,
  /** Muted copper. */
  copper: {color: PALETTE.copper, roughness: 0.44, metalness: 0.8} as StandardMat,
  /** Natural light wood. */
  wood: {color: PALETTE.wood, roughness: 0.62, metalness: 0} as StandardMat,
  /** Colored satin/rubber cable jacket. */
  rubber: (color: string = PALETTE.rubber): StandardMat => ({
    color,
    roughness: 0.84,
    metalness: 0.04,
  }),
  /** Pale teaching glass core: translucent but clearly visible. */
  core: (color: string = PALETTE.coreWhite, opacity = 0.82): StandardMat => ({
    color,
    roughness: 0.34,
    metalness: 0,
    transparent: true,
    opacity,
    emissive: color,
    emissiveIntensity: 0.12,
  }),
  /** Translucent light glass/fiber. */
  glass: (tint: string = PALETTE.glassClad, opacity = 0.5): StandardMat => ({
    color: tint,
    roughness: 0.12,
    metalness: 0,
    transparent: true,
    opacity,
    emissive: tint,
    emissiveIntensity: 0.18,
  }),
  /** Emissive semantic accent — reserved for light, data, energy, signals. */
  accent: (color: string, intensity = 1.5): StandardMat => ({
    color,
    roughness: 0.3,
    metalness: 0,
    emissive: color,
    emissiveIntensity: intensity,
    toneMapped: false,
  }),
} as const;

// Soft cinematic light rig: key from front-top, cool rim from behind for
// separation, warm fill. Used to create depth without over-brightening.
export const LIGHT = {
  ambient: {color: '#cfe0f2', intensity: 0.5},
  key: {color: '#ffffff', intensity: 1.15},
  rim: {color: '#bcd8ff', intensity: 0.9},
  fill: {color: '#ffe8c0', intensity: 0.35},
} as const;
