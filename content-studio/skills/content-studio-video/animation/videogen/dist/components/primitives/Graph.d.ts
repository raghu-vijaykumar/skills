import React from 'react';
import { type Point, type PathKind } from '../../animation/path.ts';
export type CardState = 'idle' | 'ready' | 'done' | 'stuck';
export declare function NodeCard({ p, label, state, badge, order, ring, shake, dim, appear, width, height, fontSize, solid, }: {
    p: Point;
    label: string;
    state: CardState;
    badge?: number;
    order?: number;
    ring?: boolean;
    shake?: number;
    dim?: boolean;
    appear?: number;
    width?: number;
    height?: number;
    fontSize?: number;
    solid?: boolean;
}): React.JSX.Element;
export declare function DirectedEdge({ from, to, opacity, color, width, pulse, kind, waypoints, }: {
    from: Point;
    to: Point;
    opacity: number;
    color?: string;
    width?: number;
    pulse?: {
        t: number;
        speed: number;
    };
    kind?: PathKind;
    waypoints?: Point[];
}): React.JSX.Element;
export declare function ChipSlots({ order, count, y, label, x, width, height, slotW, slotH, names, }: {
    order: number[];
    count: number;
    y: number;
    label: string;
    x: number;
    width: number;
    height: number;
    slotW?: number;
    slotH?: number;
    names: (i: number) => string;
}): React.JSX.Element;
