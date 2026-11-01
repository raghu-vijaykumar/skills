import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Database} from './Database.tsx';

export const DATABASE_PREVIEW_DURATION_FRAMES = 150;
export const DATABASE_PREVIEW_FPS = 30;

export function DatabasePreview() {
  const frame = useCurrentFrame();
  const t = frame / 30;
  let state: any = 'idle';
  let trans: any = undefined;
  let contents: Array<{key: string; value?: string; status?: any}> = [];

  if (t < 1) state = 'idle';
  else if (t < 2) {
    const p = Math.min(1, (t - 1) / 0.8);
    trans = {from: 'idle', to: 'writing', progress: p};
    state = 'writing';
    contents = [{key: 'pay_8F3A', status: 'writing'}];
  } else if (t < 3) {
    state = 'writing';
    contents = [{key: 'pay_8F3A', status: 'writing'}];
  } else {
    state = 'contains-record';
    contents = [
      {key: 'pay_8F3A', value: 'SUCCESS · $100', status: 'ok'},
      {key: 'pay_7F1C', value: 'FAILED', status: 'missing'},
    ];
  }

  return (
    <AbsoluteFill style={{background: '#05070a', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{position: 'relative', width: 960, height: 540}}>
        <div style={{position: 'absolute', left: 330, top: 150}}>
          <Database x={0} y={0} name="PRIMARY DB" label="MASTER · STRONG CONSISTENCY" state={state} transition={trans} contents={contents} />
        </div>
        <div style={{position: 'absolute', bottom: 40, left: 0, right: 0, textAlign: 'center', color: '#8B949E', fontSize: 13}}>
          IDLE → WRITE → RECORD STORED (responsive contents)
        </div>
      </div>
    </AbsoluteFill>
  );
}
