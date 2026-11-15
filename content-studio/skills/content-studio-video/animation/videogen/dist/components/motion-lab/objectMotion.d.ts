import React, { type ReactNode } from 'react';
export type Pose = {
    x?: number;
    y?: number;
    scale?: number;
    angle?: number;
    opacity?: number;
};
export type MotionKey = Pose & {
    frame: number;
    ease?: 'linear' | 'hold';
};
export declare function progress(frame: number, from: number, to: number): number;
export declare function smooth(frame: number, from: number, to: number): number;
export declare function samplePose(keys: readonly MotionKey[], frame: number): Required<Pose>;
export declare function MotionObject({ frame, keys, children }: {
    frame: number;
    keys: readonly MotionKey[];
    children: ReactNode;
}): React.JSX.Element;
export type Point = readonly [number, number];
/** A packet travels along a visible route. A lost response can stop mid-route. */
export declare function RoutedPacket({ frame, from, to, start, end, color, stop, children }: {
    frame: number;
    from: Point;
    to: Point;
    start: number;
    end: number;
    color: string;
    stop?: number;
    children?: ReactNode;
}): React.JSX.Element;
