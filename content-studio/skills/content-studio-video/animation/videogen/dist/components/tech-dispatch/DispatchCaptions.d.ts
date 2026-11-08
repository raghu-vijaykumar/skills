import React from 'react';
export declare function DispatchCaptions({ cues, fontSize }: {
    cues: readonly {
        id: string;
        text: string;
        startSeconds: number;
        endSeconds: number;
    }[];
    fontSize?: number;
}): React.JSX.Element | null;
