import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

// A scene plan carries story semantics; this renderer supplies reusable visual grammar.
// Drafts may replace one representation with an authored component without changing timing.
export type ExplainerScene = {
  id: string; type: 'hero' | 'device' | 'flow' | 'stack' | 'code' | 'data' | 'document' | 'presenter';
  startFrame: number; endFrame: number; title: string; kicker?: string; subtitle?: string;
  visual: {symbol?: string; nodes?: string[]; lines?: string[]; metric?: string; note?: string; labels?: string[];
    theme?: 'light' | 'dark'; imageId?: string};
  stateChanges: {frame: number; label: string}[];
  camera: {frame: number; scale: number; x?: number; y?: number}[];
  presenter?: {pose?: 'speaking' | 'pointing' | 'thinking' | 'none'; label?: string};
  assetIds: string[]; narrationCueIds: string[]; sourceIds: string[]; audioCueIds: string[];
};
export type ExplainerPlan = {schemaVersion: 1; width: number; height: number; fps: 30; durationFrames: number; title?: string;
  chapters?: {label: string; startFrame: number}[]; scenes: ExplainerScene[]};

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const ease = (n: number) => {const x = clamp(n); return x * x * (3 - 2 * x);};
const blue = '#6bc8ff';
const violet = '#a68cff';
const white = '#f2f5ff';
const panel = 'linear-gradient(145deg,#192139 0%,#0a1023 55%,#070a14 100%)';

const box: React.CSSProperties = {border: '1px solid #91a8e044', borderRadius: 26, background: panel,
  boxShadow: '0 38px 90px #0009, inset 0 1px #e3eeff2b'};

function activeState(scene: ExplainerScene, frame: number) {
  let index = 0;
  for (let i = 0; i < scene.stateChanges.length; i++) if (frame >= scene.stateChanges[i].frame) index = i;
  return index;
}

function cameraAt(scene: ExplainerScene, frame: number) {
  const keys = scene.camera;
  if (frame <= keys[0].frame) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    if (frame <= keys[i].frame) {
      const a = keys[i - 1], b = keys[i], t = ease((frame - a.frame) / (b.frame - a.frame));
      return {scale: a.scale + (b.scale - a.scale) * t, x: (a.x ?? 0) + ((b.x ?? 0) - (a.x ?? 0)) * t,
        y: (a.y ?? 0) + ((b.y ?? 0) - (a.y ?? 0)) * t};
    }
  }
  return keys[keys.length - 1];
}

function Presenter({pose = 'speaking', label, w, h, frame, image}: {pose?: string; label?: string; w: number; h: number; frame: number; image?: string}) {
  if (pose === 'none') return null;
  if (image) {
    const portrait = w < h;
    return <div style={{position: 'absolute', left: portrait ? '54%' : undefined, right: portrait ? undefined : 12,
      bottom: portrait ? -18 : -10, width: portrait ? 630 : 410,
      transform: portrait ? 'translateX(-50%)' : undefined, zIndex: 8,
      filter: 'drop-shadow(0 22px 30px #0009)'}}>
      <img src={image} style={{width: '100%', display: 'block'}}/>
      {label && <div style={{position:'absolute',right:0,bottom:25,color:white,fontWeight:800,fontSize:18}}>{label}</div>}
    </div>;
  }
  const size = Math.min(w * (w < h ? 0.38 : 0.18), h * 0.25);
  const wave = Math.sin(frame * 0.13) * 5;
  return <div style={{position: 'absolute', right: w < h ? 48 : 68, bottom: w < h ? 44 : 38,
    width: size, height: size * 1.12, filter: 'drop-shadow(0 20px 22px #0008)', zIndex: 8}}>
    <svg width="100%" height="100%" viewBox="0 0 300 330" aria-label="Original illustrated presenter">
      <defs><linearGradient id="coat" x2="0.8" y2="1"><stop stopColor="#5571b7"/><stop offset="1" stopColor="#1b2c54"/></linearGradient>
        <linearGradient id="face" x2="0.8" y2="1"><stop stopColor="#f3be97"/><stop offset="1" stopColor="#bf785e"/></linearGradient></defs>
      <ellipse cx="150" cy="314" rx="112" ry="13" fill="#02050f" opacity="0.55"/>
      <path d="M54 302 Q56 198 111 190 L188 190 Q246 204 250 302 Z" fill="url(#coat)" stroke="#869fe0" strokeWidth="3"/>
      <path d="M122 193 L148 252 L176 193" fill="#111a32" stroke="#b7ccff" strokeWidth="3"/>
      <path d="M129 190 L139 215 L160 221 L174 190" fill="url(#face)"/>
      <ellipse cx="151" cy="118" rx="74" ry="83" fill="url(#face)" stroke="#f5d6bd" strokeWidth="2"/>
      <path d="M75 111 Q77 23 153 26 Q230 20 226 104 Q209 67 174 63 Q126 83 75 111" fill="#17213d"/>
      <path d="M77 110 Q72 74 101 52 Q89 99 85 131" fill="#10192e"/>
      <path d="M205 72 Q239 91 223 143 L216 123" fill="#10192e"/>
      <path d="M105 127 Q128 117 143 127 M166 127 Q182 118 202 126" fill="none" stroke="#5a3a3a" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="126" cy="131" r="5" fill="#1d2536"/><circle cx="182" cy="130" r="5" fill="#1d2536"/>
      <path d="M147 143 Q144 160 154 160" fill="none" stroke="#a96355" strokeWidth="3"/>
      <path d={pose === 'thinking' ? 'M135 178 Q154 171 172 178' : 'M135 175 Q152 187 174 174'} fill="none" stroke="#703f42" strokeWidth="4" strokeLinecap="round"/>
      <path d={pose === 'pointing' ? `M215 223 Q255 ${183 + wave} 266 ${130 + wave} L279 ${112 + wave}` : `M222 228 Q260 ${252 + wave} 265 ${277 + wave}`}
        fill="none" stroke="#435b99" strokeWidth="31" strokeLinecap="round"/>
      <circle cx="270" cy={pose === 'pointing' ? 113 + wave : 278 + wave} r="16" fill="url(#face)"/>
    </svg>
    {label && <div style={{position: 'absolute', right: 0, bottom: 5, color: white, fontSize: Math.max(15, size * 0.064),
      fontWeight: 700, letterSpacing: 1, textShadow: '0 2px 8px #000'}}>{label}</div>}
  </div>;
}

function Hero({scene, w, h, frame, active}: {scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const labels = scene.visual.labels ?? scene.visual.nodes ?? [];
  const d = w < h ? w * 0.72 : Math.min(w, h) * 0.62;
  return <div style={{position: 'absolute', left: '50%', top: w < h ? '52.5%' : '55%', width: d, height: d, transform: 'translate(-50%,-50%)', perspective: 1100}}>
    {[3, 2, 1].map((z) => <div key={z} style={{position: 'absolute', inset: d * (0.08 + z * 0.055), borderRadius: '50%',
      border: `2px solid ${z === active + 1 ? blue : '#819ce0'}`, opacity: 0.18 + (4 - z) * 0.1,
      transform: `rotateX(${65 + z * 5}deg) rotateZ(${frame * (z % 2 ? 0.28 : -0.19)}deg)`,
      boxShadow: `0 0 28px ${blue}44`}} />)}
    <div style={{position: 'absolute', inset: d * 0.18, borderRadius: d * 0.13, ...box,
      transform: `rotateY(${Math.sin(frame * 0.017) * 10}deg) rotateX(-9deg)`,
      display: 'grid', placeItems: 'center', background: 'linear-gradient(135deg,#28375f,#0c1431 58%,#080b1a)',
      boxShadow: '28px 30px 0 #080e21, 34px 44px 75px #000a, inset -12px -10px 35px #0005, inset 9px 7px 25px #a1c5ff2e'}}>
      <div style={{fontSize: d * 0.32, fontWeight: 900, color: white, textShadow: `0 0 40px ${blue}`}}>{scene.visual.symbol ?? '✦'}</div>
    </div>
    {labels.slice(0, 4).map((label, i) => {
      const x = [0.05, 0.74, 0.03, 0.73][i], y = [0.1, 0.16, 0.79, 0.77][i];
      return <div key={i} style={{position: 'absolute', left: d * x, top: d * y, padding: '10px 17px', borderRadius: 13,
        color: i <= active ? white : '#9cabc9', background: '#1a2540e8', border: `1px solid ${i <= active ? blue : '#6f83b366'}`,
        fontSize: Math.max(17, d * 0.044), fontWeight: 700, transform: `translateY(${Math.sin(frame * 0.05 + i) * 8}px)`,
        boxShadow: i <= active ? `0 0 24px ${blue}55` : '0 14px 30px #0008'}}>{label}</div>;
    })}
  </div>;
}

function Device({scene, w, h, frame, active}: {scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const portrait = w < h, dw = portrait ? w * 0.72 : w * 0.59, dh = portrait ? h * 0.32 : h * 0.51;
  const lines = scene.visual.lines ?? scene.visual.nodes ?? [];
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '52%' : '55%', width: dw, height: dh,
    transform: `translate(-50%,-50%) rotateY(${Math.sin(frame * 0.012) * 4}deg)`, ...box, overflow: 'hidden'}}>
    <div style={{height: 47, background: '#202a43', borderBottom: '1px solid #8298cf55', display: 'flex', alignItems: 'center', gap: 9, padding: '0 22px'}}>
      {['#ff7076','#ffd66e','#62d5a5'].map((c,i)=><span key={i} style={{width: 11,height: 11,borderRadius: '50%',background:c}}/>)}
      <div style={{marginLeft: 22, background: '#0d172d', borderRadius: 8, flex: 1, padding: '5px 16px', color: '#adc8e6', fontSize: 17}}>{scene.visual.note ?? 'https://example.dev/app'}</div>
    </div>
    <div style={{padding: portrait ? 28 : 34}}>
      <div style={{height: 9, width: '28%', borderRadius: 5, background: blue, opacity: 0.9, marginBottom: 22}}/>
      {lines.slice(0, 5).map((line,i)=><div key={i} style={{display: 'flex', alignItems: 'center', height: portrait ? 54 : 62,
        padding: '0 18px', marginBottom: 9, borderRadius: 12, background: i === active % Math.max(1,lines.length) ? '#32507f' : '#17223c',
        border: `1px solid ${i === active % Math.max(1,lines.length) ? blue : '#435477'}`,
        transform: `translateX(${(1-ease((frame-scene.startFrame-i*5)/18))*30}px)`, color: white,
        fontSize: portrait ? 24 : 28, fontWeight: i === active ? 800 : 500}}><span style={{color: violet, marginRight: 18}}>0{i+1}</span>{line}</div>)}
    </div>
    <div style={{position: 'absolute', bottom: 0, left: 0, width: `${(active + 1) / scene.stateChanges.length * 100}%`, height: 7, background: blue, boxShadow: `0 0 20px ${blue}`}}/>
  </div>;
}

function Flow({scene, w, h, frame, active}: {scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const nodes = (scene.visual.nodes ?? []).slice(0, 5), portrait = w < h;
  const step = portrait ? Math.min(470, w * 0.7) : Math.min(265, w * 0.15);
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '50%' : '55%', display: 'flex',
    flexDirection: portrait ? 'column' : 'row', gap: portrait ? 14 : 30, transform: 'translate(-50%,-50%)', alignItems: 'center'}}>
    {nodes.map((node,i)=><React.Fragment key={i}>
      {i > 0 && <div style={{width: portrait ? 5 : 42, height: portrait ? 29 : 5, borderRadius: 5,
        background: i <= active ? blue : '#526482', boxShadow: i <= active ? `0 0 22px ${blue}` : undefined}}/>}
      <div style={{width: step, minHeight: portrait ? 107 : 130, padding: portrait ? '14px 28px' : '15px 12px', ...box, boxSizing: 'border-box',
        borderColor: i <= active ? blue : '#7790b75d', boxShadow: i <= active ? `0 0 35px ${blue}55, 0 25px 45px #0007` : '0 20px 40px #0006',
        transform: `translateY(${Math.sin(frame * 0.04 + i) * 4}px)`, display: 'grid', placeItems: 'center',
        textAlign: 'center', color: white, fontSize: portrait ? 29 : 26, fontWeight: 800,
        background: i <= active ? 'linear-gradient(125deg,#243e6a,#0c1731)' : panel}}>
          <div><span style={{color:blue,fontFamily:'monospace',fontSize:portrait?19:16,marginRight:14}}>{String(i+1).padStart(2,'0')}</span>{node}</div></div>
    </React.Fragment>)}
  </div>;
}

function Stack({scene, w, h, frame, active}: {scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const labels = (scene.visual.nodes ?? scene.visual.labels ?? []).slice(0, 5);
  const sw = Math.min(w * 0.64, 700), portrait = w < h;
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '50%' : '57%', width: sw, height: labels.length * 95 + 100,
    transform: 'translate(-50%,-50%)', perspective: 1400}}>
    {labels.map((label,i)=><div key={i} style={{position: 'absolute', left: i * 14, top: i * 97, width: sw - i * 28, height: 105,
      transform: `rotateX(48deg) rotateZ(-8deg) translateY(${Math.sin(frame * 0.025 + i) * 5}px)`,
      borderRadius: 16, background: `linear-gradient(120deg,${i <= active ? '#4966a6' : '#263352'},#0c1430)`,
      border: `2px solid ${i <= active ? blue : '#7088ba'}`, boxShadow: '14px 18px 0 #080e21, 20px 28px 40px #0009',
      display: 'flex', alignItems: 'center', paddingLeft: 38, color: white, fontSize: portrait ? 27 : 30, fontWeight: 800}}>
      <span style={{color: blue, marginRight: 30, fontFamily: 'monospace'}}>0{i+1}</span>{label}</div>)}
  </div>;
}

function Code({scene, w, h, active}: {scene: ExplainerScene; w: number; h: number; active: number}) {
  const lines = (scene.visual.lines ?? []).slice(0, 9), portrait = w < h;
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '51%' : '57%', width: portrait ? w * 0.78 : w * 0.68,
    transform: 'translate(-50%,-50%)', ...box, padding: 33, boxSizing: 'border-box'}}>
    <div style={{fontFamily: 'monospace', color: '#a4b5cf', fontSize: 19, marginBottom: 25}}>● &nbsp; TERMINAL / EXPLAINER</div>
    {lines.map((line,i)=><div key={i} style={{fontFamily: 'Consolas, monospace', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere',
      fontSize: portrait ? 24 : 30, lineHeight: 1.52, padding: '5px 12px', borderRadius: 7,
      background: i === active % Math.max(1,lines.length) ? '#425a9777' : 'transparent', color: i === active % Math.max(1,lines.length) ? white : '#a8cbec'}}>
      <span style={{color: '#6f829d', marginRight: 22}}>{String(i+1).padStart(2,'0')}</span>{line}</div>)}
  </div>;
}

function Data({scene, w, h, frame, active}: {scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const nodes = (scene.visual.nodes ?? scene.visual.labels ?? []).slice(0, 7), portrait = w < h;
  const width = portrait ? w * 0.78 : w * 0.67;
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '52%' : '58%', width, height: portrait ? 450 : 380,
    transform: 'translate(-50%,-50%)', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: 16}}>
    {nodes.map((label,i)=><div key={i} style={{flex: 1, textAlign: 'center', color: white}}>
      <div style={{height: (110 + ((i*79+57)%210)) * ease((frame-scene.startFrame-i*5)/25), borderRadius: '13px 13px 0 0',
        background: i <= active ? 'linear-gradient(#9bdfff,#4569b8)' : 'linear-gradient(#475d8d,#202c50)',
        boxShadow: i <= active ? `0 0 30px ${blue}66` : undefined}}/>
      <div style={{fontSize: portrait ? 18 : 22, paddingTop: 13, fontWeight: 700}}>{label}</div></div>)}
  </div>;
}

function Document({scene, w, h, active}: {scene: ExplainerScene; w: number; h: number; active: number}) {
  const lines = (scene.visual.lines ?? scene.visual.nodes ?? []).slice(0, 6), portrait = w < h;
  return <div style={{position: 'absolute', left: '50%', top: portrait ? '51%' : '56%', transform: 'translate(-50%,-50%)',
    width: portrait ? w * 0.73 : w * 0.57, padding: portrait ? 50 : 60, boxSizing: 'border-box',
    borderRadius: 22, background: '#f7f8fb', color: '#20304b', boxShadow: '30px 40px 0 #1d2943, 40px 65px 85px #0008'}}>
    <div style={{height: 15, width: '34%', background: '#5a7bb6', borderRadius: 6, marginBottom: 38}}/>
    {lines.map((line,i)=><div key={i} style={{padding: '16px 0', borderBottom: '1px solid #d5ddeb', display: 'flex', alignItems: 'center',
      fontSize: portrait ? 25 : 29, fontWeight: i === active ? 800 : 500}}><span style={{marginRight: 20, color: i <= active ? '#356ed2' : '#8a98b2'}}>{i <= active ? '✓' : '○'}</span>{line}</div>)}
  </div>;
}

function HeroArtwork({src, scene, w, h, frame, active}: {src: string; scene: ExplainerScene; w: number; h: number; frame: number; active: number}) {
  const portrait = w < h, local = frame - scene.startFrame, length = scene.endFrame - scene.startFrame;
  const x = Math.sin(local * 0.018) * (portrait ? 13 : 22);
  const y = Math.cos(local * 0.021) * 9;
  const scale = 0.96 + 0.12 * local / length;
  // Reserve clearance above the portrait object for the chapter path even at
  // the final camera push; leave the state label below it readable.
  const size = portrait ? 680 : 720;
  return <div style={{position:'absolute',left:'50%',top:portrait?'53.5%':'62%',width:size,height:size,
    transform:`translate(-50%,-50%) translate(${x}px,${y}px) scale(${scale})`, display:'grid',placeItems:'center'}}>
    <div style={{position:'absolute',width:size*0.64,height:size*0.64,borderRadius:'50%',background:'#508cff33',filter:'blur(80px)'}}/>
    <img src={src} style={{position:'relative',maxWidth:'100%',maxHeight:'100%',objectFit:'contain',
      filter:'drop-shadow(0 28px 30px #0009)'}}/>
    <div style={{position:'absolute',right:'9%',bottom:'10%',width:22,height:22,borderRadius:'50%',
      background:active>0?blue:'#273d64',border:`3px solid ${blue}`,boxShadow:`0 0 18px ${blue}77`}}/>
  </div>;
}

export function ExplainerFilm({plan, renderScene, presenterImage, presenterImages, media}: {plan: ExplainerPlan;
  renderScene?: (scene: ExplainerScene, frame: number) => React.ReactNode; presenterImage?: string;
  presenterImages?: Partial<Record<'speaking' | 'pointing' | 'thinking', string>>; media?: Record<string,string>}) {
  const frame = useCurrentFrame(), scene = plan.scenes.find((s) => frame >= s.startFrame && frame < s.endFrame);
  if (!scene) return <AbsoluteFill style={{background: '#050816'}}/>;
  const {width: w, height: h} = plan, portrait = w < h, local = frame - scene.startFrame;
  const active = activeState(scene, frame), cam = cameraAt(scene, frame), light = scene.visual.theme === 'light';
  const accent = light ? '#3465be' : blue, titleSize = portrait ? 61 : 70;
  const estimatedTitleRows = Math.ceil(scene.title.length / (portrait ? 26 : 39));
  const subtitleTop = portrait ? Math.max(390, 202 + estimatedTitleRows * 75 + 16) : 125 + estimatedTitleRows * 78 + 12;
  // A scene cut must contain a readable object on its first frame; a full
  // fade-to-black per beat creates unintended blank flashes in rapid explainers.
  const opacity = 0.82 + 0.18 * ease(local / 9);
  if (scene.visual.imageId && !media?.[scene.visual.imageId]) throw new Error(`Missing hero image ${scene.visual.imageId}`);
  const representation = renderScene?.(scene, frame) ?? (scene.visual.imageId ?
    <HeroArtwork src={media![scene.visual.imageId]} scene={scene} w={w} h={h} frame={frame} active={active}/> :
    ({hero: <Hero scene={scene} w={w} h={h} frame={frame} active={active}/>,
    device: <Device scene={scene} w={w} h={h} frame={frame} active={active}/>, flow: <Flow scene={scene} w={w} h={h} frame={frame} active={active}/>,
    stack: <Stack scene={scene} w={w} h={h} frame={frame} active={active}/>, code: <Code scene={scene} w={w} h={h} active={active}/>,
    data: <Data scene={scene} w={w} h={h} frame={frame} active={active}/>, document: <Document scene={scene} w={w} h={h} active={active}/>,
    presenter: <Hero scene={scene} w={w} h={h} frame={frame} active={active}/>})[scene.type]);
  return <AbsoluteFill style={{background: light ? 'radial-gradient(circle at 50% 44%,#e0e9fb,#a9bddb 80%)' :
    'radial-gradient(circle at 50% 44%,#1a2a4b,#080e20 59%,#050713)', color: light ? '#172441' : white,
    fontFamily: 'Arial, Helvetica, sans-serif', overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: 0, opacity: light ? 0.13 : 0.15,
      backgroundImage: 'linear-gradient(#a6baff40 1px,transparent 1px),linear-gradient(90deg,#a6baff40 1px,transparent 1px)',
      backgroundSize: portrait ? '70px 70px' : '82px 82px', transform: `translate(${frame * -0.17}px,${frame * 0.1}px)`}}/>
    <div style={{position: 'absolute', top: portrait ? 94 : 54, left: portrait ? 74 : 95, color: accent, fontSize: portrait ? 21 : 22,
      letterSpacing: 6, fontWeight: 800}}>{scene.kicker ?? 'CORE EXPLAINER'} &nbsp; / &nbsp; {String(plan.scenes.indexOf(scene)+1).padStart(2,'0')}</div>
    <div style={{position: 'absolute', left: portrait ? 74 : 95, right: portrait ? 74 : 120, top: portrait ? 202 : 125,
      fontSize: titleSize, lineHeight: 1.05, letterSpacing: -2.5, fontWeight: 900, maxWidth: portrait ? 930 : 1440,
      textShadow: light ? 'none' : '0 10px 40px #0009', opacity:0.75+0.25*ease(local/13),
      transform:`translateY(${(1-ease(local/13))*25}px)`}}>{scene.title}</div>
    {scene.subtitle && <div style={{position: 'absolute', left: portrait ? 78 : 99, top: subtitleTop,
      maxWidth: portrait ? 900 : 1400, fontSize: portrait ? 28 : 31, lineHeight: 1.32, color: light ? '#465877' : '#b9c6e0'}}>{scene.subtitle}</div>}
    {portrait && plan.chapters && <div style={{position:'absolute',top:495,left:72,width:w-144,height:78,display:'flex',alignItems:'flex-start',zIndex:9}}>
      <div style={{position:'absolute',left:30,right:30,top:16,height:2,background:light?'#5f7da45c':'#8fbfff6b'}}/>
      {plan.chapters.map((chapter,i)=><div key={i} style={{position:'relative',flex:1,textAlign:'center',color:frame>=chapter.startFrame?accent:(light?'#70829f':'#8394b3'),fontSize:14,fontWeight:800,letterSpacing:1}}>
        <div style={{width:19,height:19,margin:'7px auto 13px',borderRadius:'50%',background:frame>=chapter.startFrame?accent:(light?'#c5d1e2':'#1f3257'),
          border:`3px solid ${frame>=chapter.startFrame?accent:'#7594c0'}`,boxShadow:frame>=chapter.startFrame?`0 0 15px ${accent}`:undefined}}/>{chapter.label}</div>)}
    </div>}
    <div style={{position: 'absolute', inset: 0, transform: `translate(${cam.x ?? 0}px,${cam.y ?? 0}px) scale(${cam.scale})`, transformOrigin: '50% 53%', opacity}}>{representation}</div>
    <div style={{position: 'absolute', left: portrait ? 74 : 95, bottom: portrait ? 500 : 105,
      maxWidth: portrait ? 780 : 1300, fontSize: portrait ? 34 : 38, fontWeight: 800, lineHeight: 1.17,
      color: accent, textShadow: light ? 'none' : '0 6px 24px #000b'}}>{scene.stateChanges[active].label}</div>
    {scene.visual.metric && <div style={{position: 'absolute', left: portrait ? 74 : 95, bottom: portrait ? 450 : 61,
      color: light ? '#5d6f90' : '#8ea4c9', fontFamily: 'Consolas,monospace', fontSize: portrait ? 22 : 19}}>{scene.visual.metric}</div>}
    {/* Different original cutouts can express each planned pose without using reference character frames. */}
    <Presenter pose={scene.presenter?.pose ?? 'speaking'} label={scene.presenter?.label} w={w} h={h} frame={frame}
      image={presenterImages?.[scene.presenter?.pose === 'pointing' || scene.presenter?.pose === 'thinking' ? scene.presenter.pose : 'speaking'] ?? presenterImage}/>
    <div style={{position: 'absolute', left: 0, bottom: 0, height: portrait ? 9 : 7, background: accent,
      width: `${frame / plan.durationFrames * 100}%`, boxShadow: `0 0 20px ${accent}`}}/>
  </AbsoluteFill>;
}
