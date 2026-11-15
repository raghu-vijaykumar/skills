import React from 'react';
import {PURPLE} from '../../design/color.ts';

export type StackLayer = {label: string; color?: string; detail?: string};
export type LayeredStackProps = {
  now: number;
  start: number;
  layers: readonly StackLayer[];
  x?: number;
  y?: number;
  width?: number;
  gap?: number;
  accent?: string;
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

// Separating the cards in screen space makes a system stack legible at portrait size.
export function LayeredStack({now, start, layers, x = 545, y = 820, width = 440, gap = 92, accent = PURPLE}: LayeredStackProps) {
  const p = clamp01((now - start) / 0.8);
  const spread = p * p * (3 - 2 * p);
  return (
    <div style={{position: 'absolute', left: x, top: y, width, height: 620, transform: 'translateX(-50%)', perspective: 900}}>
      {layers.map((layer, index) => {
        const lift = (layers.length - index - 1) * gap * spread;
        return (
          <div key={`${layer.label}-${index}`} style={{position: 'absolute', left: 0, top: 200 + index * 15 - lift, width, height: 105, background: `linear-gradient(135deg, ${layer.color ?? '#24252e'}, #08090e)`, border: '2px solid #777985', borderRadius: 7, boxShadow: '0 16px 25px #0008', transform: 'rotateX(55deg) rotateZ(-14deg)', color: '#fff', padding: '14px 22px', boxSizing: 'border-box'}}>
            <div style={{fontSize: 21, fontWeight: 800}}>{layer.label}</div>
            <div style={{fontSize: 13, color: accent, fontFamily: 'Consolas, monospace'}}>{layer.detail}</div>
          </div>
        );
      })}
    </div>
  );
}
