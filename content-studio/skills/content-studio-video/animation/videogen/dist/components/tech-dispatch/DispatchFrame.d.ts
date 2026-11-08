import React from 'react';
export type DispatchSource = {
    src: string;
    kind?: 'image' | 'video';
    source: string;
    label: string;
    startFrom?: number;
    sequenceFrom?: number;
};
export declare function DispatchFrame({ children, chapter, footer }: {
    children: React.ReactNode;
    chapter: string;
    footer?: string;
}): React.JSX.Element;
export declare function DispatchHeadline({ eyebrow, children }: {
    eyebrow: string;
    children: React.ReactNode;
}): React.JSX.Element;
export declare function EvidencePlate({ asset, x, y, w, h, frame, radius }: {
    asset: DispatchSource;
    x: number;
    y: number;
    w: number;
    h: number;
    frame?: number;
    radius?: number;
}): React.JSX.Element;
