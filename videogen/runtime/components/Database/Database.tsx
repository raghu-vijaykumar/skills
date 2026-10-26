import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type DatabaseState = 'idle' | 'active' | 'writing' | 'contains-record';
export type DatabaseTransition = {from: DatabaseState; to: DatabaseState; progress: number};

export type DatabaseContent = {
  key: string;
  value?: string;
  status?: 'ok' | 'missing' | 'writing';
};

type Props = {
  x: number;
  y: number;
  name?: string;
  label?: string;
  state?: DatabaseState;
  transition?: DatabaseTransition;
  contents?: DatabaseContent[];
  scale?: number;
  compact?: boolean;
};

const COLORS = {
  bg: '#0d1117',
  bgLight: '#161b22',
  cyan: '#58A6FF',
  green: '#3FB950',
  red: '#F85149',
  muted: '#8B949E',
  text: '#F0F6FC',
  track: '#30363d',
};

export function Database({
  x,
  y,
  name = 'DATABASE',
  label = 'DB',
  state,
  transition,
  contents = [],
  scale = 1,
  compact = false,
}: Props) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const appear = spring({frame, fps, config: {damping: 18, stiffness: 170}});

  // Responsive state derived from contents if no explicit state given
  let resolvedState: DatabaseState = state ?? 'idle';
  if (!state) {
    if (contents.some((c) => c.status === 'writing')) resolvedState = 'writing';
    else if (contents.length > 0) resolvedState = 'contains-record';
  }

  const from = transition?.from ?? resolvedState;
  const to = transition?.to ?? resolvedState;
  const t = Math.max(0, Math.min(1, transition?.progress ?? 1));

  let displayState = resolvedState;
  let borderColor = COLORS.track;
  let status = 'IDLE';
  let statusColor = COLORS.muted;

  if (transition) {
    if (from === 'idle' && to === 'active') {
      status = t < 0.5 ? 'IDLE' : 'ACTIVE';
      borderColor = t < 0.5 ? COLORS.track : COLORS.cyan;
      statusColor = t < 0.5 ? COLORS.muted : COLORS.cyan;
      displayState = t < 0.5 ? 'idle' : 'active';
    } else if (from === 'active' && to === 'writing') {
      status = t < 0.5 ? 'ACTIVE' : 'WRITING';
      borderColor = t < 0.5 ? COLORS.cyan : COLORS.cyan;
      statusColor = t < 0.5 ? COLORS.cyan : COLORS.cyan;
      displayState = t < 0.5 ? 'active' : 'writing';
    } else if (from === 'idle' && to === 'writing') {
      status = t < 0.5 ? 'IDLE' : 'WRITING';
      borderColor = t < 0.5 ? COLORS.track : COLORS.cyan;
      statusColor = t < 0.5 ? COLORS.muted : COLORS.cyan;
      displayState = t < 0.5 ? 'idle' : 'writing';
    } else if (from === 'writing' && to === 'contains-record') {
      status = t < 0.5 ? 'WRITING' : 'RECORD STORED';
      borderColor = t < 0.5 ? COLORS.cyan : COLORS.green;
      statusColor = t < 0.5 ? COLORS.cyan : COLORS.green;
      displayState = t < 0.5 ? 'writing' : 'contains-record';
    }
  } else {
    switch (displayState) {
      case 'idle':
        status = 'IDLE';
        borderColor = COLORS.track;
        statusColor = COLORS.muted;
        break;
      case 'active':
        status = 'ACTIVE';
        borderColor = COLORS.cyan;
        statusColor = COLORS.cyan;
        break;
      case 'writing':
        status = 'WRITING';
        borderColor = COLORS.cyan;
        statusColor = COLORS.cyan;
        break;
      case 'contains-record':
        status = 'RECORD STORED';
        borderColor = COLORS.green;
        statusColor = COLORS.green;
        break;
    }
  }

  const pulsing = displayState === 'writing' || displayState === 'active';
  const pulse = pulsing ? 1 + Math.sin(frame * 0.25) * 0.03 : 1;
  const width = compact ? 130 : 300;
  const contentRows = contents.length > 0 ? contents : null;
  const lidHeight = compact ? 8 : 12;
  const pad = compact ? '10px 10px 14px' : '16px 16px 22px';

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width,
        transform: `scale(${scale * appear * pulse})`,
        transformOrigin: 'center',
      }}
    >
      {/* Top ellipse lid */}
      <div
        style={{
          height: lidHeight,
          border: `2px solid ${borderColor}`,
          borderBottom: 'none',
          borderRadius: `${width / 2}px ${width / 2}px 0 0 / ${lidHeight}px ${lidHeight}px 0 0`,
          background: COLORS.bgLight,
          boxSizing: 'border-box',
          boxShadow: `inset 0 -2px 4px rgba(0,0,0,0.4), 0 0 14px ${borderColor}22`,
        }}
      />
      {/* Cylinder body */}
      <div
        style={{
          border: `2px solid ${borderColor}`,
          borderTop: 'none',
          borderRadius: `0 0 ${width / 2}px ${width / 2}px / 0 0 ${lidHeight * 2.5}px ${lidHeight * 2.5}px`,
          background: COLORS.bg,
          padding: pad,
          boxSizing: 'border-box',
          boxShadow: `0 0 14px ${borderColor}44`,
        }}
      >
        <div style={{display: 'flex', alignItems: 'flex-start', gap: 8}}>
          <div style={{width: compact ? 22 : 36, height: compact ? 22 : 36, borderRadius: 8, background: '#161b22', border: `2px solid ${borderColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: compact ? 10 : 16, flexShrink: 0}}>◉</div>
          <div style={{minWidth: 0, flex: 1}}>
            <div style={{fontSize: compact ? 10 : 13, fontWeight: 800, letterSpacing: 1, color: COLORS.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{name}</div>
            <div style={{fontSize: compact ? 8 : 10, color: COLORS.muted, letterSpacing: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 1}}>{label}</div>
          </div>
          <div style={{marginLeft: 'auto', marginTop: 2, fontSize: compact ? 8 : 10, fontWeight: 800, letterSpacing: 1, color: statusColor, border: `1px solid ${statusColor}`, padding: '3px 6px', borderRadius: 6, whiteSpace: 'nowrap', flexShrink: 0}}>{status}</div>
        </div>

        {/* Contents area — empty space, fills responsively with contents */}
        <div
          style={{
            marginTop: compact ? 8 : 14,
            minHeight: compact ? 28 : 48,
            borderRadius: 8,
            background: '#161b22',
            border: `1px solid ${borderColor}33`,
            padding: compact ? 6 : 10,
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: 4,
            overflow: 'hidden',
          }}
        >
          {displayState === 'writing' && !contentRows && (
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
              <div style={{flex: 1, height: 4, background: '#30363d', borderRadius: 4, overflow: 'hidden'}}>
                <div style={{width: `${30 + (transition?.progress ?? 0) * 70}%`, height: '100%', background: COLORS.cyan}} />
              </div>
              <div style={{fontSize: compact ? 9 : 11, color: COLORS.cyan, fontFamily: 'monospace'}}>writing…</div>
            </div>
          )}
          {contentRows && (
            contentRows.map((row, i) => {
              const rowColor =
                row.status === 'ok' ? COLORS.green :
                row.status === 'missing' ? COLORS.red :
                row.status === 'writing' ? COLORS.cyan :
                COLORS.text;
              const marker = row.status === 'missing' ? '✕' : row.status === 'writing' ? '…' : '✓';
              return (
                <div key={i} style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, fontFamily: 'monospace', fontSize: compact ? 9 : 12, color: COLORS.text, padding: '2px 4px', borderRadius: 4, background: '#0d1117'}}>
                  <span style={{display: 'flex', alignItems: 'center', gap: 4}}>
                    <span style={{color: rowColor, fontWeight: 700}}>{marker}</span>
                    {row.key}
                  </span>
                  {row.value && <span style={{fontSize: compact ? 8 : 10, color: COLORS.muted}}>{row.value}</span>}
                </div>
              );
            })
          )}
          {displayState === 'idle' && !contentRows && (
            <div style={{fontSize: compact ? 9 : 12, color: COLORS.muted, fontFamily: 'monospace', textAlign: 'center'}}>∅ empty</div>
          )}
        </div>

        <div style={{marginTop: compact ? 6 : 10, display: 'flex', gap: 4}}>
          {(['idle', 'active', 'writing', 'contains-record'] as const).map((s, i) => {
            const lit = (displayState === 'idle' && s === 'idle') || (displayState === 'active' && i <= 1) || (displayState === 'writing' && i <= 2) || displayState === 'contains-record';
            return <div key={s} style={{flex: 1, height: 3, borderRadius: 3, background: lit ? borderColor : '#30363d'}} />;
          })}
        </div>
      </div>
    </div>
  );
}
