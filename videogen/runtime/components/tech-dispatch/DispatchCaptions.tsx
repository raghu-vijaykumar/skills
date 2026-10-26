import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {TECH_DISPATCH as D} from '../../design/techDispatch.ts';

export function DispatchCaptions({cues, fontSize = 40}: {cues: readonly {id: string; text: string; startSeconds: number; endSeconds: number}[]; fontSize?: number}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = frame / fps;
  const active = cues.find((cue) => now >= cue.startSeconds && now < cue.endSeconds);
  if (!active) return null;
  const words = active.text.split(/\s+/);
  const spoken = Math.min(words.length, Math.floor(((now - active.startSeconds) / Math.max(0.001, active.endSeconds - active.startSeconds)) * words.length) + 1);
  return <div data-captions style={{position: 'absolute', top: 156, left: 65, right: 65, minHeight: 115, display: 'flex', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap', gap: '0 8px', textAlign: 'center', lineHeight: 1.28, zIndex: 70, fontFamily: D.sans, pointerEvents: 'none'}}>
    {words.map((word, index) => <span key={`${active.id}-${index}`} style={{fontSize, fontWeight: 800, color: index === spoken - 1 ? D.onAccent : index < spoken ? D.text : D.muted, opacity: index < spoken ? 1 : 0.52, background: index === spoken - 1 ? D.marker : 'transparent', padding: index === spoken - 1 ? '2px 6px' : 0, borderRadius: 3}}>{word}</span>)}
  </div>;
}
