import React from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

export type OverlayProps = {
  accent?: string;
  subscribeColor?: string;
  textColor?: string;
  scale?: number;
  bottom?: number;
  labels?: [string, string, string];
};
const clamp = {extrapolateLeft:"clamp" as const,extrapolateRight:"clamp" as const};
const Icon = ({type}:{type:"like"|"share"|"play"|"bell"}) => {
  const common={width:32,height:32,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round" as const,strokeLinejoin:"round" as const};
  return <svg {...common} aria-hidden>{type==="like"?<path d="M7 10v11H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3Zm0 0 5-8a2 2 0 0 1 3 2l-1 6h6a2 2 0 0 1 2 2l-2 8a2 2 0 0 1-2 1H7"/>:type==="share"?<><path d="M12 5v14M5 12l7-7 7 7"/><path d="M5 19h14"/></>:type==="play"?<path d="m9 6 9 6-9 6V6Z" fill="currentColor" stroke="none"/>:<><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/></>}</svg>;
};
export const LikeShareSubscribe:React.FC<OverlayProps> = ({
  accent="#5b7cfa",subscribeColor="#ed333b",textColor="#fff",scale=1,bottom=90,
  labels=["LIKE","SHARE","SUBSCRIBE"]
})=>{
  const frame=useCurrentFrame();
  const {fps,durationInFrames}=useVideoConfig();
  const enter=spring({frame,fps,config:{damping:17,stiffness:115}});
  const exit=interpolate(frame,[Math.max(0,durationInFrames-12),durationInFrames],[1,0],clamp);
  const pop=(at:number)=>spring({frame:frame-at,fps,config:{damping:9,stiffness:190}});
  const bell=interpolate(frame,[70,74,78,82,86],[0,-16,13,-8,0],clamp);
  return <AbsoluteFill style={{pointerEvents:"none",justifyContent:"flex-end",alignItems:"center",paddingBottom:bottom}}>
    <div style={{display:"flex",alignItems:"center",gap:16,padding:"14px 22px",borderRadius:100,
      background:"rgba(10,16,36,.91)",border:`2px solid ${accent}`,boxShadow:`0 12px 35px rgba(0,0,0,.35)`,
      color:textColor,fontFamily:"Arial, sans-serif",fontWeight:800,fontSize:24,letterSpacing:1,
      opacity:exit,transform:`translateY(${(1-enter)*95}px) scale(${scale*(.8+.2*enter)})`}}>
      <span style={{display:"flex",alignItems:"center",gap:8,transform:`scale(${1+.13*Math.max(0,pop(15)-.4)})`}}><Icon type="like"/>{labels[0]}</span>
      <span style={{opacity:.4}}>│</span>
      <span style={{display:"flex",alignItems:"center",gap:8,transform:`scale(${1+.1*Math.max(0,pop(32)-.4)})`}}><Icon type="share"/>{labels[1]}</span>
      <span style={{background:subscribeColor,borderRadius:80,padding:"10px 16px",display:"flex",alignItems:"center",gap:7,
        transform:`scale(${1+.12*Math.max(0,pop(52)-.4)})`}}><Icon type="play"/>{labels[2]}</span>
      <span style={{transform:`rotate(${bell}deg)`,transformOrigin:"top center",color:"#ffcd47"}}><Icon type="bell"/></span>
    </div>
  </AbsoluteFill>;
};
