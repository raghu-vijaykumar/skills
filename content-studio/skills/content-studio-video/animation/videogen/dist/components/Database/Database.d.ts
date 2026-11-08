import React from 'react';
export type DatabaseState = 'idle' | 'active' | 'writing' | 'contains-record';
export type DatabaseTransition = {
    from: DatabaseState;
    to: DatabaseState;
    progress: number;
};
export type DatabaseContent = {
    key: string;
    value?: string;
    status?: 'ok' | 'missing' | 'writing';
};
type Props = {
    x: number;
    y: number;
    name?: string;
    label?: string;
    state?: DatabaseState;
    transition?: DatabaseTransition;
    contents?: DatabaseContent[];
    scale?: number;
    compact?: boolean;
};
export declare function Database({ x, y, name, label, state, transition, contents, scale, compact, }: Props): React.JSX.Element;
export {};
