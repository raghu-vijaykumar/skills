// Deterministic, original low-level score and transition accents from scene timing.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {validateScenePlan} from './scene-plan.mjs';

const clamp = (x) => Math.max(-1, Math.min(1, x));
const chords = [[130.81,155.56,196.00],[103.83,130.81,155.56],[155.56,196.00,233.08],[116.54,146.83,174.61]];
const TWO_PI = Math.PI * 2;

export function writeScoreWav(plan, output, sampleRate = 24000) {
  if (plan.fps !== 30 || !Number.isInteger(plan.durationFrames)) throw new Error('A 30 fps scene plan is required');
  const duration = plan.durationFrames / plan.fps;
  const samples = Math.round(duration * sampleRate);
  fs.mkdirSync(path.dirname(output), {recursive: true});
  const fd = fs.openSync(output, 'w');
  const head = Buffer.alloc(44);
  head.write('RIFF',0); head.writeUInt32LE(36 + samples*2,4); head.write('WAVEfmt ',8);
  head.writeUInt32LE(16,16); head.writeUInt16LE(1,20); head.writeUInt16LE(1,22);
  head.writeUInt32LE(sampleRate,24); head.writeUInt32LE(sampleRate*2,28);
  head.writeUInt16LE(2,32); head.writeUInt16LE(16,34); head.write('data',36); head.writeUInt32LE(samples*2,40);
  fs.writeSync(fd, head);
  const transitions = plan.scenes.map((s)=>s.startFrame/plan.fps).slice(1);
  const states = plan.scenes.flatMap((s)=>s.stateChanges.map((c)=>c.frame/plan.fps));
  let ti = 0, si = 0, seed = 1729, noiseFiltered = 0;
  const chunkSamples = 16384;
  try {
    for (let offset=0; offset<samples; offset += chunkSamples) {
      const n = Math.min(chunkSamples,samples-offset), chunk=Buffer.alloc(n*2);
      for (let j=0;j<n;j++) {
        const t=(offset+j)/sampleRate;
        while (ti+1<transitions.length && transitions[ti+1] < t) ti++;
        while (si+1<states.length && states[si+1] < t) si++;
        const chord=chords[Math.floor(t/8)%chords.length];
        const fade=Math.min(1,t/1.2,(duration-t)/1.5);
        const breathing=0.86+0.14*Math.sin(TWO_PI*t/9);
        let pad=0;
        for (let k=0;k<3;k++) pad += Math.sin(TWO_PI*chord[k]*t + 0.09*Math.sin(TWO_PI*t*(0.13+k*0.03)))/3;
        const bass=Math.sin(TWO_PI*(chord[0]/2)*t)*0.18;
        const beat=t%0.5, pluck=Math.exp(-beat*17)*Math.sin(TWO_PI*chord[(Math.floor(t*2)%3)]*2*t)*0.13;
        seed=(Math.imul(seed,1664525)+1013904223)>>>0;
        const white=(seed/0xffffffff)*2-1;
        noiseFiltered=0.96*noiseFiltered+0.04*white;
        const event=transitions[ti] ?? -100;
        const dt=t-event;
        const whoosh=dt>-0.25 && dt<0.25 ? (1-Math.abs(dt)/0.25)*noiseFiltered*0.24 : 0;
        const state=states[si] ?? -100;
        const ds=t-state;
        const click=ds>=0 && ds<0.09 ? Math.exp(-ds*65)*Math.sin(TWO_PI*740*ds)*0.12 : 0;
        const sample=clamp(((pad*0.26+bass+pluck)*breathing+whoosh+click)*fade);
        chunk.writeInt16LE(Math.round(sample*32767),j*2);
      }
      fs.writeSync(fd,chunk);
    }
  } finally {fs.closeSync(fd);}
  return {duration,samples,sampleRate};
}

export function generateScore(folder) {
  const checked=validateScenePlan(folder);
  if (!checked) throw new Error('scene-plan.json is required');
  const out=path.join(folder,'assets','generated','audio','score.mp3');
  const wav=path.join(folder,'assets','generated','audio','.score.wav');
  try {
    const result=writeScoreWav(checked.plan,wav);
    const ffmpeg=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-i',wav,'-c:a','libmp3lame','-b:a','160k',out],{encoding:'utf8'});
    if(ffmpeg.error||ffmpeg.status!==0)throw new Error(`Score encode failed: ${ffmpeg.stderr || ffmpeg.error?.message}`);
    return {out,...result};
  } finally {if(fs.existsSync(wav))fs.unlinkSync(wav);}
}
