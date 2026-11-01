import React from 'react';
import {Audio, Img, Sequence, Video} from 'remotion';
import type {MediaClip} from '../../animation/media.ts';

// Mounts declared MediaClips (sfx/image/gif/video) as Remotion <Sequence>s so
// media and SFX are deterministic first-class elements of a composition.
export function MediaLayer({clips, fps}: {clips: readonly MediaClip[]; fps: number}) {
  return (
    <>
      {clips.map((clip) => {
        const from = Math.round(clip.start * fps);
        const frames = Math.max(1, Math.round(clip.duration * fps));
        if (clip.kind === 'sfx') {
          return (
            <Sequence key={clip.id} from={from} durationInFrames={frames}>
              <Audio src={clip.src} volume={clip.volume ?? 0.5} />
            </Sequence>
          );
        }
        if (clip.kind === 'video') {
          return (
            <Sequence key={clip.id} from={from} durationInFrames={frames}>
              <Video src={clip.src} style={{position: 'absolute', inset: 0}} />
            </Sequence>
          );
        }
        return (
          <Sequence key={clip.id} from={from} durationInFrames={frames}>
            <Img src={clip.src} style={{position: 'absolute', inset: 0}} />
          </Sequence>
        );
      })}
    </>
  );
}
