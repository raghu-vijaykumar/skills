import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

export type LinkState = 'active' | 'success' | 'failed' | 'disconnected';
export type LinkDirection = 'right' | 'left' | 'both' | 'none';

type Props = {
  x: number;
  y: number;
  width: number;
  height?: number;
  source?: string;
  target?: string;
  direction?: LinkDirection;
  label?: string;
  state?: LinkState;
  progress?: number;
  animated?: boolean;
  // legacy compat
  active?: boolean;
  failed?: boolean;
};

const COLORS: Record<LinkState, string> = {
  active: '#58A6FF',
  success: '#3FB950',
  failed: '#F85149',
  disconnected: '#F85149',
};

export function Link({
  x,
  y,
  width,
  height = 30,
  direction = 'right',
  label,
  state = 'active',
  progress,
  animated = false,
  active,
  failed,
}: Props) {
  const frame = useCurrentFrame();
  // Resolve legacy props
  let resolvedState = state;
  if (typeof failed === 'boolean' && failed) resolvedState = 'failed';
  else if (typeof active === 'boolean' && !active) resolvedState = 'success';
  const color = COLORS[resolvedState] ?? COLORS.active;
  const isFailed = resolvedState === 'failed' || resolvedState === 'disconnected';
  const isDisconnected = resolvedState === 'disconnected';

  const drawProgress = typeof progress === 'number' ? Math.max(0, Math.min(1, progress)) : 1;
  const visibleWidth = width * drawProgress;
  const travel = ((frame % 36) / 36);
  // No dot by default — only when explicitly requested
  const dotVisible = animated && (resolvedState === 'active' || resolvedState === 'failed' || resolvedState === 'success');
  const dotX = direction === 'left' ? width * (1 - travel) : width * travel;

  return (
    <div style={{position: 'absolute', left: x, top: y, width, height, pointerEvents: 'none', overflow: 'hidden'}}>
      {/* track */}
      <div style={{position: 'absolute', left: 0, top: 13, width, height: 3, background: `${color}22`, borderRadius: 3, border: isDisconnected ? `1px dashed ${color}` : 'none'}} />
      {/* progress */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 13,
          width: visibleWidth,
          height: 3,
          background: isDisconnected ? 'transparent' : color,
          boxShadow: isDisconnected ? 'none' : `0 0 14px ${color}`,
          borderRadius: 3,
          opacity: drawProgress > 0 ? 1 : 0,
          borderTop: isDisconnected ? `2px dashed ${color}` : 'none',
          borderBottom: isDisconnected ? `2px dashed ${color}` : 'none',
          backgroundImage: isDisconnected ? `repeating-linear-gradient(90deg, ${color} 0 8px, transparent 8px 12px)` : undefined,
        }}
      />
      {/* traveling dot */}
      {dotVisible && drawProgress > 0.05 && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(dotX, visibleWidth) - 6,
            top: 7,
            width: 15,
            height: 15,
            borderRadius: '50%',
            background: color,
            boxShadow: `0 0 16px ${color}`,
            opacity: isDisconnected ? 0.5 : 1,
          }}
        />
      )}
      {/* arrow */}
      {(direction === 'right' || direction === 'both') && (
        <div
          style={{
            position: 'absolute',
            right: -1,
            top: 7,
            width: 0,
            height: 0,
            borderTop: '6px solid transparent',
            borderBottom: '6px solid transparent',
            borderLeft: `10px solid ${color}`,
            opacity: drawProgress > 0.98 ? 1 : 0,
          }}
        />
      )}
      {(direction === 'left' || direction === 'both') && (
        <div
          style={{
            position: 'absolute',
            left: -1,
            top: 7,
            width: 0,
            height: 0,
            borderTop: '6px solid transparent',
            borderBottom: '6px solid transparent',
            borderRight: `10px solid ${color}`,
            opacity: drawProgress > 0.98 ? 1 : 0,
          }}
        />
      )}
      {/* label */}
      {label && (
        <div
          style={{
            position: 'absolute',
            left: width / 2,
            top: -8,
            transform: 'translateX(-50%)',
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: 1,
            color,
            background: '#0d1117',
            padding: '2px 6px',
            borderRadius: 6,
            border: `1px solid ${color}55`,
            whiteSpace: 'nowrap',
            opacity: drawProgress > 0.2 ? 1 : 0,
          }}
        >
          {label}
        </div>
      )}
      {/* X for failed/disconnected */}
      {isFailed && drawProgress > 0.5 && (
        <div
          style={{
            position: 'absolute',
            left: width / 2 - 10,
            top: 2,
            fontSize: 18,
            fontWeight: 900,
            color,
            opacity: 0.9,
          }}
        >
          ×
        </div>
      )}
    </div>
  );
}
