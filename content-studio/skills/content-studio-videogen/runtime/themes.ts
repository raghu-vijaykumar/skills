import {defineTheme} from './project.ts';

// Neutral is the default for new projects. Channel branding is an explicit choice.
export const neutralTheme = defineTheme({
  id: 'neutral',
  brand: '',
  colors: {
    background: '#101820', elevated: '#1b2732', text: '#f7f9fb',
    muted: '#a9b5bf', border: '#475663', accent: '#57c7ff',
    success: '#66dcac', warning: '#ffd166', danger: '#ff6b78',
  },
  fonts: {sans: 'Arial, sans-serif', mono: 'Consolas, monospace'},
  typography: {title: 52, kicker: 26, caption: 40, minimumContent: 24},
  bands: {captionY: 0.115, titleTop: 56, titleSide: 72, contentPadding: 48},
});

// This preset matches the source tokens in the current Revise Labs films.
export const reviseLabsTheme = defineTheme({
  id: 'revise-labs',
  brand: 'REVISE LABS',
  colors: {
    background: '#05070a', elevated: '#0d1117', text: '#f4f8fd',
    muted: '#9aa7b8', border: '#3a4554', accent: '#00e0ff',
    success: '#2bff88', warning: '#ffd400', danger: '#ff3355',
  },
  fonts: {
    sans: "'Inter', 'Segoe UI', Arial, sans-serif",
    mono: "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace",
  },
  typography: {title: 52, kicker: 26, caption: 40, minimumContent: 24},
  bands: {captionY: 0.115, titleTop: 56, titleSide: 72, contentPadding: 48},
});
