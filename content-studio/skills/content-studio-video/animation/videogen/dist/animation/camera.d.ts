import type { EasingName } from './types.ts';
export type Rect = {
    x: number;
    y: number;
    w: number;
    h: number;
};
export type Point = {
    x: number;
    y: number;
};
export type CameraTransform = {
    cx: number;
    cy: number;
    scale: number;
};
export declare const identityTransform: (width: number, height: number) => CameraTransform;
export type CameraShotType = 'establish' | 'focus' | 'zoom' | 'pan' | 'track' | 'follow' | 'compare' | 'return' | 'pushin' | 'pullout' | 'slide' | 'orbit' | 'drift' | 'dolly' | 'macro' | 'pullback' | 'shake' | 'whip' | 'handoff';
export type CameraKey = {
    t: number;
} & CameraTransform;
export type CameraShot = {
    id: string;
    op: CameraShotType;
    start: number;
    duration: number;
    easing: EasingName;
    keys: CameraKey[];
    region?: Rect;
};
export declare function fitRegion(region: Rect, width: number, height: number, margin?: number, minScale?: number, maxScale?: number): CameraTransform;
export declare const centerPoint: (region: Rect) => Point;
export declare const unionRects: (regions: Rect[]) => Rect;
export declare const lerpTransform: (a: CameraTransform, b: CameraTransform, u: number) => CameraTransform;
export type FitOptions = {
    margin?: number;
    minScale?: number;
    maxScale?: number;
};
export declare function establish(id: string, region: Rect, start: number, duration: number | undefined, width: number, height: number, opts?: FitOptions): CameraShot;
export declare function focus(id: string, region: Rect, start: number, duration: number | undefined, width: number, height: number, opts?: FitOptions): CameraShot;
export declare function zoom(id: string, region: Rect, start: number, duration: number | undefined, width: number, height: number, opts?: FitOptions): CameraShot;
export declare function pan(id: string, from: Point, to: Point, start: number, duration: number | undefined, width: number, height: number, scale?: number): CameraShot;
export declare function track(id: string, waypoints: {
    at: number;
    region: Rect;
}[], start: number, width: number, height: number, opts?: FitOptions): CameraShot;
export declare function follow(id: string, regionAt: (t: number) => Rect, start: number, duration: number, width: number, height: number, opts?: FitOptions, step?: number): CameraShot;
export declare function compare(id: string, regions: Rect[], start: number, duration: number | undefined, width: number, height: number, opts?: FitOptions): CameraShot;
export declare function cameraReturn(id: string, start: number, duration: number | undefined, width: number, height: number, from?: CameraTransform): CameraShot;
export declare function cameraTransformAt(now: number, shots: readonly CameraShot[], width: number, height: number): CameraTransform;
export declare const applyTransform: (p: Point, cam: CameraTransform, width: number, height: number) => Point;
export declare const invertTransform: (p: Point, cam: CameraTransform, width: number, height: number) => Point;
export declare function cameraWorldStyle(cam: CameraTransform, width: number, height: number): {
    zoom: number;
    transform: string;
    transformOrigin: string;
};
export declare const visibleRect: (cam: CameraTransform, width: number, height: number) => Rect;
export declare const rectInView: (r: Rect, cam: CameraTransform, width: number, height: number) => boolean;
export type CameraIssue = {
    t: number;
    shot: string;
    msg: string;
    kind: 'error' | 'warn';
};
export declare function validateCamera(shots: readonly CameraShot[], width: number, height: number): CameraIssue[];
export declare function cameraTrajectory(shots: readonly CameraShot[], width: number, height: number, step?: number): {
    t: number;
    cam: CameraTransform;
}[];
