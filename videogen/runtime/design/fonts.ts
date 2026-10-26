// Self-hosted design-system fonts.
//
// The typography tokens (`src/design/typography.ts`) name `Inter` and
// `JetBrains Mono`, but the render environment has neither installed, so every
// stack silently fell back to Segoe UI / Consolas and asked for weights those
// fonts do not have — which the browser synthesized (faux bold), making graphic
// text look soft next to the title. Loading the real variable fonts here makes
// the named families resolve with their true weights in every composition.
//
// The woff2 files are committed under `public/fonts/` and served with
// `staticFile`, so the render is fully offline and deterministic (no runtime
// network fetch). Both files are variable fonts: one file covers the whole
// weight range used by the design system.
import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

export const FONT_SANS_FAMILY = 'Inter';
export const FONT_MONO_FAMILY = 'JetBrains Mono';

let started = false;

// Call once from a composition entry point. `loadFont` wraps `delayRender`,
// so Remotion waits for the faces before rendering the first frame.
export function loadAppFonts(): void {
  if (started) return;
  if (typeof document === 'undefined') return; // Node import safety
  started = true;

  loadFont({
    family: FONT_SANS_FAMILY,
    url: staticFile('fonts/inter-variable-latin.woff2'),
    weight: '100 900',
    style: 'normal',
    display: 'block',
  });

  loadFont({
    family: FONT_MONO_FAMILY,
    url: staticFile('fonts/jetbrains-mono-variable-latin.woff2'),
    weight: '100 800',
    style: 'normal',
    display: 'block',
  });
}
