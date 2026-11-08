import type { CameraTransform } from './camera.ts';
export type DepthLayer = {
    id: string;
    x: number;
    y: number;
    w: number;
    h: number;
    z: number;
};
export type DepthCamera = {
    /** Perspective focal length (canvas units). Larger = flatter/less perspective. */
    focal: number;
    /** Depth the lens focuses on (canvas units) for soft focus. */
    focusZ: number;
    /** Depth-of-field strength: blur px per canvas-unit of |z - focusZ|. 0 = off. */
    dof: number;
};
export type DepthProjection = {
    x: number;
    y: number;
    scale: number;
    w: number;
    h: number;
    zIndex: number;
    blur: number;
};
export declare const DEPTH_DEFAULTS: DepthCamera;
export declare const perspectiveScale: (z: number, focal: number) => number;
export declare function projectLayer(layer: DepthLayer, cam: CameraTransform, depth: Partial<DepthCamera>, width: number, height: number): DepthProjection;
export declare function projectLayers(layers: readonly DepthLayer[], cam: CameraTransform, depth: Partial<DepthCamera>, width: number, height: number): {
    layer: DepthLayer;
    p: DepthProjection;
}[];
export declare function rackFocus(fromZ: number, toZ: number, progress: number): number;
