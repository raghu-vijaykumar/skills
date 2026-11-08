import React from 'react';
type NarrationCue = {
    endSeconds: number;
};
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
export declare function registerVideoEntry(options: RegisterVideoEntryOptions): () => React.JSX.Element;
export declare function registerVideoCatalog(entries: RegisterVideoEntryOptions[]): () => React.JSX.Element;
export {};
