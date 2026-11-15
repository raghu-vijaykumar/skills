import React from 'react';
export type HeadlinePart = {
    text: string;
    emphasis?: boolean;
    strong?: boolean;
};
export type HeadlineCue = {
    start: number;
    end: number;
    lines: readonly (readonly HeadlinePart[])[];
};
export type KineticHeadlineProps = {
    now: number;
    cues: readonly HeadlineCue[];
    color?: string;
    muted?: string;
    accent?: string;
    fontSize?: number;
    width?: number;
    top?: number;
    selectionHandles?: boolean;
};
export declare const activeHeadlineCue: (cues: readonly HeadlineCue[], now: number) => HeadlineCue | undefined;
export declare function KineticHeadline({ now, cues, color, muted, accent, fontSize, width, top, selectionHandles, }: KineticHeadlineProps): React.JSX.Element | null;
