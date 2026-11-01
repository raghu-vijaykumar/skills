import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import RippleGrid from './RippleGrid.js';

// Full-bleed WebGL ripple-grid background for any composition (landscape or
// portrait). `fixedTime` is derived from the current frame so the shader is
// deterministic across renders (no rAF loop).
export function RippleBackground({
  gridColor = '#80acea',
  rippleIntensity = 0,
  gridSize = 23,
  gridThickness = 50,
  fadeDistance = 0.5,
  vignetteStrength = 1.5,
  glowIntensity = 0,
  opacity = 0.55,
  gridRotation = 0,
  fadeTiles = 3,
  enableRainbow = false,
  backgroundColor = '#000000',
}: {
  gridColor?: string;
  rippleIntensity?: number;
  gridSize?: number;
  gridThickness?: number;
  fadeDistance?: number;
  vignetteStrength?: number;
  glowIntensity?: number;
  opacity?: number;
  gridRotation?: number;
  fadeTiles?: number;
  enableRainbow?: boolean;
  backgroundColor?: string;
}) {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const fixedTime = frame / fps;

  return (
    <AbsoluteFill style={{backgroundColor, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 0, width, height}}>
        <RippleGrid
          enableRainbow={enableRainbow}
          gridColor={gridColor}
          rippleIntensity={rippleIntensity}
          gridSize={gridSize}
          gridThickness={gridThickness}
          fadeDistance={fadeDistance}
          vignetteStrength={vignetteStrength}
          glowIntensity={glowIntensity}
          opacity={opacity}
          gridRotation={gridRotation}
          mouseInteraction={false}
          mouseInteractionRadius={0.8}
          fixedTime={fixedTime}
          fadeTiles={fadeTiles}
          width={width}
          height={height}
        />
      </div>
    </AbsoluteFill>
  );
}

export default RippleBackground;
