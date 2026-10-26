// DepthWorld — the shared 2.5D scene surface. It projects a set of depth layers
// through the shared `DepthCamera` model (`src/animation/depth.ts`) and draws
// them as flat, axis-aligned planes at their projected screen position, scale,
// depth-sort order and soft-focus blur.
//
// Why flat planes instead of CSS `perspective`/`translateZ`: for the billboard
// layers Revise Labs stages (2D assets in 2.5D space), the projection math is
// the whole look — parallax, perspective scale, occlusion and soft focus — and
// computing it directly keeps the DOM result identical to the pure, Node-safe
// `projectLayer` numbers that validators and labels rely on. No CSS-3D
// z-fighting, no perspective-origin drift, one source of truth.
//
// Readable text never lives on a blurred/depth-scaled layer (RULES §4.12). Put
// labels on a flat overlay and position them from `projectLayer`'s output (see
// DepthLab for the pattern).

import React from 'react';
import {useVideoConfig} from 'remotion';
import {projectLayers, type DepthCamera, type DepthLayer, type DepthProjection} from '../animation/depth.ts';
import type {CameraTransform} from '../animation/camera.ts';

export function DepthWorld({
  cam,
  depth,
  layers,
  renderLayer,
}: {
  cam: CameraTransform;
  depth?: Partial<DepthCamera>;
  layers: readonly DepthLayer[];
  renderLayer: (layer: DepthLayer, p: DepthProjection) => React.ReactNode;
}) {
  const {width, height} = useVideoConfig();
  const projected = projectLayers(layers, cam, depth ?? {}, width, height);
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      {projected.map(({layer, p}) => (
        <div
          key={layer.id}
          style={{
            position: 'absolute',
            left: p.x,
            top: p.y,
            width: p.w,
            height: p.h,
            zIndex: p.zIndex,
            transformOrigin: '0 0',
            filter: p.blur > 0.05 ? `blur(${p.blur.toFixed(2)}px)` : undefined,
          }}
        >
          {renderLayer(layer, p)}
        </div>
      ))}
    </div>
  );
}
