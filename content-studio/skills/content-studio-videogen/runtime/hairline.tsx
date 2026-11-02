// Frame-driven isometric line art: seekability is required for Remotion rendering.
// Visual principles adapted from Lucas Marques's MIT-licensed Hairline project.
import React, {type ReactNode} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {Theme} from './project.ts';

export type HairlinePalette = {stroke: string; highlight: string; background: string};
export type HairlineFigureProps = {frame: number; fps: number; progress: number;
  palette: HairlinePalette; width: number; height: number};
export type HairlineStageProps = {
  frame: number; fps: number; durationInFrames: number; theme: Theme;
  figure: (props: HairlineFigureProps) => ReactNode;
  width?: number; height?: number; background?: string;
};

export function hairlineProgress(frame: number, durationInFrames: number): number {
  if (!Number.isFinite(frame) || !Number.isFinite(durationInFrames) || durationInFrames <= 1) return 0;
  const t = Math.max(0, Math.min(1, frame / (durationInFrames - 1)));
  return t * t * (3 - 2 * t);
}
export function iso(x: number, y: number, z = 0): [number, number] {
  return [(x - y) * 0.866, (x + y) * 0.5 - z];
}
export function hairlinePalette(theme: Theme): HairlinePalette {
  return {stroke: theme.colors.text, highlight: theme.colors.accent,
    background: theme.colors.background};
}

/** Pure SVG stage. The same frame always produces the same geometry. */
export function HairlineStage({frame, fps, durationInFrames, theme, figure,
  width = 1080, height = 1080, background}: HairlineStageProps) {
  const palette = hairlinePalette(theme);
  const progress = hairlineProgress(frame, durationInFrames);
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox={`0 0 ${width} ${height}`}
    width={width} height={height} role="img" aria-label="Isometric line animation"
    style={{display: 'block', background: background ?? palette.background}}>
    <g transform={`translate(${width / 2} ${height / 2 - height * 0.075})`} fill="none"
      stroke={palette.stroke} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
      {figure({frame, fps, progress, palette, width, height})}
    </g>
  </svg>;
}

/** Remotion adapter; narration and captions can be composed around this stage. */
export function HairlineSequence(props: Omit<HairlineStageProps, 'frame' | 'fps' | 'durationInFrames'> &
  {durationInFrames?: number}) {
  const frame = useCurrentFrame();
  const config = useVideoConfig();
  return <HairlineStage {...props} frame={frame} fps={config.fps}
    durationInFrames={props.durationInFrames ?? config.durationInFrames}/>;
}

/** A compact proof figure: one packet enters an opaque cache and leaves on a second rail. */
export function HairlineCacheFigure({progress, palette}: HairlineFigureProps) {
  const outgoing = progress > 0.52;
  const inputX = -290 + 280 * Math.min(1, progress / 0.52);
  const outputX = 15 + 265 * Math.max(0, (progress - 0.52) / 0.48);
  return <>
    {/* Guides go behind the solid. The body hides lines that should be occluded. */}
    <path d="M-340 145 L-85 145 L0 96 L85 145 L340 145" opacity={0.45}/>
    <path d="M-340 205 L-85 205 L0 156 L85 205 L340 205" opacity={0.3}/>
    <path d="M-105 -15 Q0 -74 105 -15 L105 115 Q0 174 -105 115 Z"
      fill={palette.background}/>
    <path d="M-105 16 Q0 75 105 16 M-105 55 Q0 114 105 55" opacity={0.55}/>
    <circle cx={inputX} cy={145} r={12} fill={palette.background}
      stroke={outgoing ? palette.stroke : palette.highlight}/>
    {outgoing && <circle cx={outputX} cy={205} r={12} fill={palette.background}
      stroke={palette.highlight}/>}
  </>;
}
