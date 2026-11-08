import React from 'react';
export type VlogEffectPreset = 'flash' | 'swipe' | 'shutter' | 'speed-lines' | 'frame-pop';
export type VlogTransitionPreset = 'crossfade' | 'slide' | 'wipe' | 'flash';
export declare function vlogProgress(frame: number, durationInFrames: number): number;
export declare const midPeak: (progress: number) => number;
export declare function swipeOffset(progress: number): number;
type EffectProps = {
    preset: VlogEffectPreset;
    durationInFrames: number;
    color?: string;
    accent?: string;
};
/** Mount inside a Sequence so the effect uses that Sequence's local frame. */
export declare function VlogEffect({ preset, durationInFrames, color, accent }: EffectProps): React.JSX.Element;
type TransitionProps = {
    preset: VlogTransitionPreset;
    durationInFrames: number;
    from: React.ReactNode;
    to: React.ReactNode;
    direction?: 'left' | 'right';
    color?: string;
    accent?: string;
};
/** Both scene nodes must cover the composition for the transition window. */
export declare function VlogTransition({ preset, durationInFrames, from, to, direction, color, accent }: TransitionProps): React.JSX.Element;
export {};
