import React from 'react';
export type StackLayer = {
    label: string;
    color?: string;
    detail?: string;
};
export type LayeredStackProps = {
    now: number;
    start: number;
    layers: readonly StackLayer[];
    x?: number;
    y?: number;
    width?: number;
    gap?: number;
    accent?: string;
};
export declare function LayeredStack({ now, start, layers, x, y, width, gap, accent }: LayeredStackProps): React.JSX.Element;
