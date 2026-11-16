import React, {type ComponentType} from 'react';
import type {WordChannels, WordChoreography} from './wordChoreography.ts';

export type WordActorArtProps = {channels: WordChannels; frame: number};
export type WordArtPreset = Readonly<Record<string, ComponentType<WordActorArtProps>>>;

/** Swap actor artwork while keeping paint order and the compiled rig values. */
export function WordMotionCast({choreography, art, frame}: {
  choreography: WordChoreography;
  art: WordArtPreset;
  frame: number;
}) {
  return <>{choreography.actorIds.map(actor => {
    if (!Object.hasOwn(art, actor) || !art[actor]) throw new Error(`Art preset is missing actor ${actor}`);
    const Art = art[actor];
    return <Art key={actor} frame={frame} channels={choreography.sample(actor, frame)}/>;
  })}</>;
}
