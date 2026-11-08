import React, { type ReactNode } from 'react';
import type { Theme } from './project.ts';
export type HairlinePalette = {
    stroke: string;
    highlight: string;
    background: string;
};
export type HairlineFigureProps = {
    frame: number;
    fps: number;
    progress: number;
    palette: HairlinePalette;
    width: number;
    height: number;
};
export type HairlineStageProps = {
    frame: number;
    fps: number;
    durationInFrames: number;
    theme: Theme;
    figure: (props: HairlineFigureProps) => ReactNode;
    width?: number;
    height?: number;
    background?: string;
};
export declare function hairlineProgress(frame: number, durationInFrames: number): number;
export declare function iso(x: number, y: number, z?: number): [number, number];
export declare function hairlinePalette(theme: Theme): HairlinePalette;
/** Pure SVG stage. The same frame always produces the same geometry. */
export declare function HairlineStage({ frame, fps, durationInFrames, theme, figure, width, height, background }: HairlineStageProps): React.JSX.Element;
/** Remotion adapter; narration and captions can be composed around this stage. */
export declare function HairlineSequence(props: Omit<HairlineStageProps, 'frame' | 'fps' | 'durationInFrames'> & {
    durationInFrames?: number;
}): React.JSX.Element;
/** A compact proof figure: one packet enters an opaque cache and leaves on a second rail. */
export declare function HairlineCacheFigure({ progress, palette }: HairlineFigureProps): React.JSX.Element;
