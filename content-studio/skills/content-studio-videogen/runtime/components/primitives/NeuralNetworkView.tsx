import React from 'react';
import {CYAN, RED, TEXT} from '../../design/color.ts';
import type {Network, NetworkState} from './neuralNetwork.ts';

// Renderer for the reusable neural-network primitive. It paints one frame of a
// `Network` from a `NetworkState` (see neuralNetwork.ts) as a flat SVG: node
// columns, a representative set of connections, and the forward/backward signal
// travelling through them. The scene owns the camera and any labels.

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
const hex = (c: string) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
const mixHex = (a: string, b: string, t: number) => {
  const pa = hex(a);
  const pb = hex(b);
  const u = clamp01(t);
  return `#${pa.map((v, i) => Math.round(v + (pb[i] - v) * u).toString(16).padStart(2, '0')).join('')}`;
};

export function NeuralNetwork({
  net,
  state,
  width,
  height,
  opacity = 1,
  tone = CYAN,
  errorTone = RED,
  weightVisible = false,
}: {
  net: Network;
  state: NetworkState;
  width: number;
  height: number;
  opacity?: number;
  tone?: string;
  errorTone?: string;
  /** Draw connections with a width driven by their weight (update beat). */
  weightVisible?: boolean;
}) {
  if (opacity < 0.02) return null;

  const edges: React.ReactNode[] = net.edges.map((e, i) => {
    const a = net.nodes[e.from];
    const b = net.nodes[e.to];
    const flow = state.edgeFlow[i] ?? 0;
    const back = state.edgeBack[i] ?? 0;
    const weight = state.edgeWeight[i] ?? e.weight;
    const base = weightVisible ? 1.2 + weight * 3.4 : 1.8;
    return (
      <line
        key={`edge-${e.id}`}
        x1={a.x}
        y1={a.y}
        x2={b.x}
        y2={b.y}
        stroke={mixHex(tone, errorTone, back * 1.15)}
        strokeWidth={base + flow * 5 + back * 5}
        strokeLinecap="round"
        opacity={opacity * (0.1 + flow * 0.55 + back * 0.6)}
      />
    );
  });

  const nodes: React.ReactNode[] = net.nodes.map((n, i) => {
    const act = state.nodeActivation[i] ?? 0;
    const back = state.nodeBack[i] ?? 0;
    const lit = clamp01(act + back);
    const r = n.r * (1 + act * 0.34 + back * 0.22);
    return (
      <g key={`node-${i}`}>
        <circle cx={n.x} cy={n.y} r={r * 1.7} fill={mixHex(tone, errorTone, back)} opacity={opacity * lit * 0.14} />
        <circle cx={n.x} cy={n.y} r={r} fill={mixHex(tone, errorTone, back * 1.15)} opacity={opacity * (0.34 + lit * 0.62)} />
        <circle cx={n.x} cy={n.y} r={r * 0.4} fill={TEXT} opacity={opacity * lit * 0.9} />
      </g>
    );
  });

  return (
    <svg width={width} height={height} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
      {edges}
      {nodes}
      {state.pulse && (
        <g>
          <circle cx={state.pulse.x} cy={state.pulse.y} r={46} fill={tone} opacity={opacity * 0.16} />
          <circle cx={state.pulse.x} cy={state.pulse.y} r={24} fill={tone} opacity={opacity * 0.6} />
          <circle cx={state.pulse.x} cy={state.pulse.y} r={13} fill={TEXT} opacity={opacity * 0.95} />
        </g>
      )}
    </svg>
  );
}
