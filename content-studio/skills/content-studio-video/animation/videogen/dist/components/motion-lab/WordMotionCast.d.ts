import React, { type ComponentType } from 'react';
import type { WordChannels, WordChoreography } from './wordChoreography.ts';
export type WordActorArtProps = {
    channels: WordChannels;
    frame: number;
};
export type WordArtPreset = Readonly<Record<string, ComponentType<WordActorArtProps>>>;
/** Swap actor artwork while keeping paint order and the compiled rig values. */
export declare function WordMotionCast({ choreography, art, frame }: {
    choreography: WordChoreography;
    art: WordArtPreset;
    frame: number;
}): React.JSX.Element;
