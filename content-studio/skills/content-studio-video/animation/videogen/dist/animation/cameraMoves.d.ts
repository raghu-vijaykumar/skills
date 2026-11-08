import type { EasingName } from './types.ts';
import { type CameraShot, type CameraTransform, type Point, type Rect } from './camera.ts';
export type MoveOptions = {
    from?: CameraTransform;
    minScale?: number;
    maxScale?: number;
    easing?: EasingName;
    intensity?: number;
};
export type FitMoveOptions = MoveOptions & {
    margin?: number;
    minScale?: number;
    maxScale?: number;
};
export declare function pushIn(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts?: FitMoveOptions): CameraShot;
export declare function snapZoom(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts?: FitMoveOptions): CameraShot;
export declare function pullOut(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts?: FitMoveOptions): CameraShot;
export declare function pullBack(id: string, region: Rect, start: number, duration: number, width: number, height: number, opts?: FitMoveOptions): CameraShot;
export type SlideOptions = MoveOptions & {
    axis?: 'x' | 'y';
    scale?: number;
};
export declare function slide(id: string, from: Point, to: Point, start: number, duration: number, width: number, height: number, opts?: SlideOptions): CameraShot;
export declare function followTarget(id: string, at: (t: number) => Point, start: number, duration: number, width: number, height: number, opts?: MoveOptions & {
    scale?: number;
    step?: number;
}): CameraShot;
export type PanBetweenOptions = MoveOptions & {
    scale?: number;
    keepBoth?: boolean;
};
export declare function panBetween(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts?: PanBetweenOptions): CameraShot;
export declare function handoffFocus(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts?: PanBetweenOptions): CameraShot;
export type OrbitOptions = MoveOptions & {
    radius?: number;
    sagitta?: number;
    scale?: number;
};
export declare function arcPan(id: string, a: Point, b: Point, start: number, duration: number, width: number, height: number, opts?: OrbitOptions): CameraShot;
export declare function orbit(id: string, pivot: Point, startDeg: number, endDeg: number, start: number, duration: number, width: number, height: number, opts?: OrbitOptions): CameraShot;
export type DollyOptions = MoveOptions & {
    toScale?: number;
    anchor?: Point;
};
export declare function dollyZoom(id: string, focal: Point, start: number, duration: number, width: number, height: number, opts?: DollyOptions): CameraShot;
export declare function macroMicroMacro(id: string, micro: Rect, start: number, duration: number, width: number, height: number, opts?: FitMoveOptions): CameraShot;
export type ShakeOptions = MoveOptions & {
    amplitude?: number;
    shakes?: number;
};
export declare function impactShake(id: string, at: CameraTransform, start: number, duration: number, width: number, height: number, opts?: ShakeOptions): CameraShot;
export type WhipOptions = PanBetweenOptions & {
    overshoot?: number;
};
export declare function whipPan(id: string, a: Point | Rect, b: Point | Rect, start: number, duration: number, width: number, height: number, opts?: WhipOptions): CameraShot;
export type DriftOptions = MoveOptions & {
    amplitude?: number;
    period?: number;
    breathing?: boolean;
};
export declare function parallaxDrift(id: string, start: number, duration: number, width: number, height: number, opts?: DriftOptions): CameraShot;
export declare function sequenceShots(shots: readonly CameraShot[]): CameraShot[];
