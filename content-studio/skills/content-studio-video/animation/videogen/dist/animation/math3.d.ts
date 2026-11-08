export type Vec3 = {
    x: number;
    y: number;
    z: number;
};
export type MathCamera = {
    target: Vec3;
    distance: number;
    yaw: number;
    pitch: number;
    fov: number;
};
export declare const MATH_CAMERA_DEFAULTS: Pick<MathCamera, 'distance' | 'yaw' | 'pitch' | 'fov'>;
export type ScreenPoint = {
    x: number;
    y: number;
    depth: number;
    scale: number;
};
export type Segment = {
    a: Vec3;
    b: Vec3;
};
export declare const v3: (x: number, y: number, z: number) => Vec3;
export declare const add3: (a: Vec3, b: Vec3) => Vec3;
export declare const sub3: (a: Vec3, b: Vec3) => Vec3;
export declare const scale3: (a: Vec3, s: number) => Vec3;
export declare const dot3: (a: Vec3, b: Vec3) => number;
export declare const cross3: (a: Vec3, b: Vec3) => Vec3;
export declare const len3: (a: Vec3) => number;
export declare const norm3: (a: Vec3) => Vec3;
export declare function mathCamera(target: Vec3, partial?: Partial<MathCamera>): MathCamera;
export type CameraBasis = {
    pos: Vec3;
    right: Vec3;
    up: Vec3;
    forward: Vec3;
};
export declare function cameraBasis(cam: MathCamera): CameraBasis;
export declare function focalLength(cam: MathCamera, height: number): number;
export type MathCameraKey = {
    t: number;
    cam: MathCamera;
};
export declare function lerpMathCamera(a: MathCamera, b: MathCamera, u: number): MathCamera;
export declare function mathCameraAt(now: number, keys: readonly MathCameraKey[]): MathCamera;
export declare function projectPoint(cam: MathCamera, p: Vec3, width: number, height: number): ScreenPoint;
export declare const NEAR_PLANE = 0.001;
export declare function isBehindCamera(cam: MathCamera, p: Vec3): boolean;
export declare function projectSegment(cam: MathCamera, seg: Segment, width: number, height: number): {
    a: ScreenPoint;
    b: ScreenPoint;
};
export declare function projectPolyline(cam: MathCamera, pts: readonly Vec3[], width: number, height: number): ScreenPoint[];
export type SurfaceGrid = {
    nx: number;
    ny: number;
    x0: number;
    x1: number;
    y0: number;
    y1: number;
    z: number[][];
};
export declare function sampleSurface(f: (x: number, y: number) => number, x0: number, x1: number, y0: number, y1: number, nx: number, ny: number): SurfaceGrid;
export declare function gridX(grid: SurfaceGrid, i: number): number;
export declare function gridY(grid: SurfaceGrid, j: number): number;
export type SurfaceQuad = {
    i: number;
    j: number;
    corners: [Vec3, Vec3, Vec3, Vec3];
    center: Vec3;
    normal: Vec3;
};
export declare function surfaceQuads(grid: SurfaceGrid): SurfaceQuad[];
export declare function lambert(normal: Vec3, light: Vec3): number;
export declare function gradient2(f: (x: number, y: number) => number, x: number, y: number, h?: number): {
    dx: number;
    dy: number;
};
export declare function steepestTangent(f: (x: number, y: number) => number, x: number, y: number, h?: number): Vec3;
export declare function contourSegments(grid: SurfaceGrid, level: number): Segment[];
export declare function chainSegments(segs: readonly Segment[], eps?: number): Vec3[][];
export declare function planeGrid(x0: number, x1: number, y0: number, y1: number, nx: number, ny: number, z?: number): Vec3[][];
export declare function axes(origin: Vec3, length: number): {
    x: Segment;
    y: Segment;
    z: Segment;
};
export declare function arrowHead(tail: Vec3, tip: Vec3, size: number, angle?: number): [Segment, Segment];
