import React, {type ReactNode} from 'react';

export type Pose = {x?: number; y?: number; scale?: number; angle?: number; opacity?: number};
export type MotionKey = Pose & {frame: number; ease?: 'linear' | 'hold'};
const defaults: Required<Pose> = {x: 0, y: 0, scale: 1, angle: 0, opacity: 1};

export function progress(frame: number, from: number, to: number) {
  if (to <= from) return frame >= to ? 1 : 0;
  return Math.max(0, Math.min(1, (frame - from) / (to - from)));
}

export function smooth(frame: number, from: number, to: number) {
  const t = progress(frame, from, to);
  return t * t * (3 - 2 * t);
}

// Keys inherit prior channels. Incoming easing lets a cut stay discrete while
// other actors in the same shot continue moving on their own tracks.
export function samplePose(keys: readonly MotionKey[], frame: number): Required<Pose> {
  let pose = defaults;
  let previousFrame: number | undefined;
  for (const key of keys) {
    const {frame: nextFrame, ease, ...channels} = key;
    const next = {...pose, ...channels};
    if (frame < nextFrame) {
      if (previousFrame === undefined) return next;
      const t = ease === 'hold' ? 0 : ease === 'linear' ? progress(frame, previousFrame, nextFrame) :
        smooth(frame, previousFrame, nextFrame);
      return {
        x: pose.x + (next.x - pose.x) * t,
        y: pose.y + (next.y - pose.y) * t,
        scale: pose.scale + (next.scale - pose.scale) * t,
        angle: pose.angle + (next.angle - pose.angle) * t,
        opacity: pose.opacity + (next.opacity - pose.opacity) * t,
      };
    }
    pose = next;
    previousFrame = nextFrame;
  }
  return pose;
}

export function MotionObject({frame, keys, children}: {
  frame: number; keys: readonly MotionKey[]; children: ReactNode;
}) {
  const pose = samplePose(keys, frame);
  return <g opacity={pose.opacity} transform={`translate(${pose.x} ${pose.y}) rotate(${pose.angle}) scale(${pose.scale})`}>
    {children}
  </g>;
}

export type Point = readonly [number, number];

/** A packet travels along a visible route. A lost response can stop mid-route. */
export function RoutedPacket({frame, from, to, start, end, color, stop = 1, children}: {
  frame: number; from: Point; to: Point; start: number; end: number;
  color: string; stop?: number; children?: ReactNode;
}) {
  const active = frame >= start && frame <= end;
  const t = progress(frame, start, end) * Math.max(0, Math.min(1, stop));
  const x = from[0] + (to[0] - from[0]) * t;
  const y = from[1] + (to[1] - from[1]) * t;
  return <g>
    <path d={`M${from[0]},${from[1]} L${to[0]},${to[1]}`} fill="none" stroke={color}
      strokeWidth={2} strokeDasharray="6 8" opacity={0.55}/>
    {active && <g transform={`translate(${x} ${y})`}>
      {children ?? <><circle r={15} fill={color} opacity={0.22}/><circle r={7} fill={color}/></>}
    </g>}
  </g>;
}
