import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {getAudioDurationInSeconds} from '@remotion/media-utils';

type NarrationCue = {endSeconds: number};

type RegisterVideoEntryOptions = {
  id: string;
  component: React.ComponentType<any>;
  narrationSrc: string;
  narrationCues: NarrationCue[];
  width?: number;
  height?: number;
  fps?: number;
  followAudioSrc?: string;
  followDurationFrames?: number;
};

function buildComposition(entry: RegisterVideoEntryOptions) {
  const {id, component, narrationSrc, narrationCues, width = 1080, height = 1920, fps = 30, followAudioSrc, followDurationFrames = 0} = entry;
  const durationSeconds = narrationCues[narrationCues.length - 1]?.endSeconds ?? 0;

  return (
    <Composition
      key={id}
      id={id}
      component={component}
      durationInFrames={Math.max(1, Math.ceil(durationSeconds * fps) + followDurationFrames)}
      fps={fps}
      width={width}
      height={height}
      calculateMetadata={async () => {
        const narrationDuration = await getAudioDurationInSeconds(narrationSrc);
        const followDuration = followAudioSrc ? await getAudioDurationInSeconds(followAudioSrc) : 0;

        return {
          durationInFrames: Math.max(1, Math.ceil(Math.max(durationSeconds, narrationDuration) * fps) + Math.ceil(followDuration * fps)),
        };
      }}
    />
  );
}

export function registerVideoEntry(options: RegisterVideoEntryOptions) {
  const Root = () => buildComposition(options);
  registerRoot(Root);
  return Root;
}

export function registerVideoCatalog(entries: RegisterVideoEntryOptions[]) {
  const Root = () => <>{entries.map((entry) => buildComposition(entry))}</>;
  registerRoot(Root);
  return Root;
}
