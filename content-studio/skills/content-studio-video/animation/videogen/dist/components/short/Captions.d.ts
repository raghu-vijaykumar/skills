import React from 'react';
export declare function Captions({ cues, y, fontSize, }: {
    cues: readonly {
        id: string;
        text: string;
        startSeconds: number;
        endSeconds: number;
    }[];
    y?: number;
    fontSize?: number;
}): React.JSX.Element | null;
