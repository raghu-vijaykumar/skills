import React from 'react';
export declare function RapidStage({ children, grid }: {
    children: React.ReactNode;
    grid?: boolean;
}): React.JSX.Element;
export declare function Slam({ lines, color, size, align, top, delay, accent }: {
    lines: string[];
    color?: string;
    size?: number;
    align?: 'left' | 'center';
    top?: number;
    delay?: number;
    accent?: number;
}): React.JSX.Element;
export declare function StatSlam({ value, label, color, size, top }: {
    value: string;
    label: string;
    color?: string;
    size?: number;
    top?: number;
}): React.JSX.Element;
export declare function SourceShot({ src, kind, source, label, startFrom, zoom, position, dim, fit, children }: {
    src: string;
    kind?: 'image' | 'video';
    source: string;
    label?: string;
    startFrom?: number;
    zoom?: number;
    position?: string;
    dim?: number;
    fit?: 'cover' | 'contain';
    children?: React.ReactNode;
}): React.JSX.Element;
export declare function BrowserFrame({ src, url, x, y, w, h, dark }: {
    src: string;
    url: string;
    x?: number;
    y?: number;
    w?: number;
    h?: number;
    dark?: boolean;
}): React.JSX.Element;
export declare function MemeCut({ src, label, startFrom, fit }: {
    src: string;
    label: string;
    startFrom?: number;
    fit?: 'cover' | 'contain';
}): React.JSX.Element;
export type AnnotationKind = 'box' | 'circle' | 'arrow' | 'underline';
export declare function Annotation({ kind, x, y, w, h, label, color, delay, to }: {
    kind: AnnotationKind;
    x: number;
    y: number;
    w: number;
    h: number;
    label?: string;
    color?: string;
    delay?: number;
    to?: [number, number];
}): React.JSX.Element;
export declare function LowerThird({ left, right, color }: {
    left: string;
    right?: string;
    color?: string;
}): React.JSX.Element;
export declare function CutFlash({ color }: {
    color?: string;
}): React.JSX.Element;
