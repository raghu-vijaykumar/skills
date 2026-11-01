import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Link} from './Link.tsx';

export const LINK_PREVIEW_DURATION_FRAMES = 150;
export const LINK_PREVIEW_FPS = 30;

const STATES: Array<{state: any; label: string}> = [
  {state: 'active', label: 'ACTIVE'},
  {state: 'success', label: 'SUCCESS'},
  {state: 'failed', label: 'FAILED'},
  {state: 'disconnected', label: 'DISCONNECTED'},
];

export function LinkPreview() {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const phase = Math.min(STATES.length - 1, Math.floor(t / 1.2));

  return (
    <AbsoluteFill style={{background: '#05070a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{position: 'relative', width: 960, height: 540}}>
        {STATES.map((item, i) => {
          const show = i <= phase;
          const y = 60 + i * 92;
          return (
            <div key={item.state} style={{position: 'absolute', left: 60, top: y, width: 840, opacity: show ? 1 : 0}}>
              <div style={{position: 'absolute', left: 0, top: 34, width: 120, fontSize: 11, fontWeight: 800, letterSpacing: 1, color: '#8B949E'}}>{item.label}</div>
              <Link
                x={180}
                y={30}
                width={520}
                state={item.state}
                direction={item.state === 'active' ? 'both' : item.state === 'failed' || item.state === 'disconnected' ? 'right' : 'right'}
                label={item.state === 'disconnected' ? 'connection lost' : item.state === 'failed' ? 'request' : 'payment'}
              />
            </div>
          );
        })}
        <div style={{position: 'absolute', bottom: 30, left: 0, right: 0, textAlign: 'center', color: '#8B949E', fontSize: 12}}>
          Link — states: active / success / failed / disconnected
        </div>
      </div>
    </AbsoluteFill>
  );
}
