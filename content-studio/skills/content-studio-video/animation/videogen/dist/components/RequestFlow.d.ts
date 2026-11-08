import React from 'react';
export type RequestWaypoint = {
    x: number;
    y: number;
    label: string;
};
export type RequestFlowProps = {
    now: number;
    waypoints: readonly RequestWaypoint[];
    /** Seconds at which the request leaves the first waypoint. */
    start: number;
    /** Seconds spent travelling each leg. */
    hop: number;
    tone?: string;
    /** Vertical arc applied mid-leg, for a sense of travel. */
    arc?: number;
    /** Draw the dashed trail behind the request. */
    trail?: boolean;
    /** Canvas size for the trail SVG. */
    width?: number;
    height?: number;
    fontSize?: number;
};
export declare function RequestFlow({ now, waypoints, start, hop, tone, arc, trail, width, height, fontSize, }: RequestFlowProps): React.JSX.Element | null;
