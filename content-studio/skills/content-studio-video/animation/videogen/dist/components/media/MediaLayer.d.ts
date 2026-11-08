import React from 'react';
import type { MediaClip } from '../../animation/media.ts';
export declare function MediaLayer({ clips, fps }: {
    clips: readonly MediaClip[];
    fps: number;
}): React.JSX.Element;
