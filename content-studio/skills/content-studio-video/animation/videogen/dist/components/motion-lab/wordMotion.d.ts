import React from 'react';
export type WordMotionCue = {
    /** Frame indexes on the same clock as the rendered scene and narration. */
    startFrame: number;
    endFrame: number;
    text: string;
    line: number;
    actor: string;
    action: string;
};
/** Find the spoken word on the scene clock. Holds keep the last word visible. */
export declare function sampleWordMotion(cues: readonly WordMotionCue[], frame: number): {
    cue: WordMotionCue;
    index: number;
    elapsed: number;
    speaking: boolean;
};
export declare function WordMotionCaption({ cues, frame, color, muted, accent }: {
    cues: readonly WordMotionCue[];
    frame: number;
    color?: string;
    muted?: string;
    accent?: string;
}): React.JSX.Element | null;
