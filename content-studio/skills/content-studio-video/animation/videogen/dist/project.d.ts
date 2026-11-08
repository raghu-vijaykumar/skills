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
    fonts: {
        sans: string;
        mono: string;
    };
    typography: {
        title: number;
        kicker: number;
        caption: number;
        minimumContent: number;
    };
    bands: {
        captionY: number;
        titleTop: number;
        titleSide: number;
        contentPadding: number;
    };
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
    publishedDirs?: string[];
    contentDir: string;
    publicDir?: string;
    workDir?: string;
    sourceCacheDir?: string;
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
        instagram?: {
            tokenFile?: string;
            apiVersion?: string;
        };
    };
};
export declare function defineTheme<const T extends Theme>(theme: T): T;
export declare function defineContentStyle<const T extends ContentStyle>(style: T): T;
export declare function defineProject<const T extends VideogenProject>(project: T): T;
