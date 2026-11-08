import React from 'react';
import { type DepthCamera, type DepthLayer, type DepthProjection } from '../animation/depth.ts';
import type { CameraTransform } from '../animation/camera.ts';
export declare function DepthWorld({ cam, depth, layers, renderLayer, }: {
    cam: CameraTransform;
    depth?: Partial<DepthCamera>;
    layers: readonly DepthLayer[];
    renderLayer: (layer: DepthLayer, p: DepthProjection) => React.ReactNode;
}): React.JSX.Element;
