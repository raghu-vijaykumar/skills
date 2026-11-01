import React from 'react';
import {AbsoluteFill} from 'remotion';

// Shared frame for all videos: a white glowing border drawn at the exact edge
// of the canvas (not inset), plus a content padding zone so scenes never
// collide with the border. Wrap the video's scenes inside <VideoFrame>.
export function VideoFrame({children, glowColor = '#ffffff'}: {children: React.ReactNode; glowColor?: string}) {
  return (
    <AbsoluteFill>
      {children}
      {/* Glow border pinned to the exact edges (0,0 .. w,h) */}
      <div
        data-layout-id="video-border"
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          border: `3px solid ${glowColor}`,
          boxShadow: `inset 0 0 22px ${glowColor}55, inset 0 0 8px ${glowColor}88`,
          borderRadius: 6,
          zIndex: 9999,
        }}
      />
    </AbsoluteFill>
  );
}
