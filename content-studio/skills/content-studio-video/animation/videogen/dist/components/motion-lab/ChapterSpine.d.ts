import React from 'react';
export type ChapterMarker = {
    label: string;
    start: number;
};
export type ChapterSpineProps = {
    now: number;
    markers: readonly ChapterMarker[];
    dark?: boolean;
    accent?: string;
    top?: number;
    width?: number;
};
export declare function ChapterSpine({ now, markers, dark, accent, top, width }: ChapterSpineProps): React.JSX.Element | null;
