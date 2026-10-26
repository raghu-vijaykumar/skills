// Project metadata is the sole bridge from a content repository to the renderer.
// No video identifier, filesystem root, or channel identity is baked into the CLI.
export type Theme = {
  id: string;
  brand: string;
  colors: {
    background: string;
    elevated: string;
    text: string;
    muted: string;
    border: string;
    accent: string;
    success: string;
    warning: string;
    danger: string;
  };
  fonts: {sans: string; mono: string};
  typography: {title: number; kicker: number; caption: number; minimumContent: number};
  bands: {captionY: number; titleTop: number; titleSide: number; contentPadding: number};
};

export type ContentStyle = {
  id: string;
  name: string;
  formats: readonly ('video' | 'carousel' | 'post')[];
  requiresFirsthandEvidence?: boolean;
};

export type ProjectCheck = {
  name: string;
  command: string;
  args?: string[];
  appliesTo?: 'video' | 'content' | 'all';
  phase?: 'prepare' | 'validate';
  whenExists?: string;
  whenFormat?: 'portrait' | 'landscape';
};

export type VideogenProject = {
  entryPoint: string;
  entryPointForVideo?: (videoId: string) => string;
  videosDir: string;
  contentDir: string;
  contentEntryPoint?: string;
  theme: Theme;
  styles: readonly ContentStyle[];
  checks?: readonly ProjectCheck[];
  renderShortSide?: number;
  browserExecutable?: string;
  publish?: {
    youtube?: {
      clientFile?: string;
      tokenFile?: string;
      categoryId?: string;
    };
  };
};

export function defineTheme<const T extends Theme>(theme: T): T {
  return theme;
}

export function defineContentStyle<const T extends ContentStyle>(style: T): T {
  return style;
}

export function defineProject<const T extends VideogenProject>(project: T): T {
  return project;
}
