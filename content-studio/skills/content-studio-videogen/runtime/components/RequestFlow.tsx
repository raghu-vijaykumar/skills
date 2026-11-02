import React from 'react';

// RequestFlow: a reusable information-request primitive for Revise Labs videos.
//
// One request object travels a fixed list of waypoints and *changes its label
// at every hop*. That morphing is the teaching device: it shows a single intent
// becoming a tool call, a command, a query or a result as it crosses a system
// boundary. Use it for AI agents, tool calling, RAG, API requests, database
// queries, CDN requests, search, queue hand-offs, and anything else where the
// same work is called something different at each layer.
//
// Deterministic: a pure function of `now` (seconds). No state, no randomness.
//
//   <RequestFlow
//     now={now}
//     start={phraseStart}
//     hop={1.1}
//     tone={BLUE}
//     waypoints={[
//       {x: 200, y: 400, label: 'intent: turn off outside lights'},
//       {x: 540, y: 400, label: 'tool call: run_command'},
//       {x: 880, y: 400, label: 'command: outside_lights → off'},
//     ]}
//   />

export type RequestWaypoint = {x: number; y: number; label: string};

export type RequestFlowProps = {
  now: number;
  waypoints: readonly RequestWaypoint[];
  /** Seconds at which the request leaves the first waypoint. */
  start: number;
  /** Seconds spent travelling each leg. */
  hop: number;
  tone?: string;
  /** Vertical arc applied mid-leg, for a sense of travel. */
  arc?: number;
  /** Draw the dashed trail behind the request. */
  trail?: boolean;
  /** Canvas size for the trail SVG. */
  width?: number;
  height?: number;
  fontSize?: number;
};

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const easeIO = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);

export function RequestFlow({
  now,
  waypoints,
  start,
  hop,
  tone = '#1a73e8',
  arc = 0,
  trail = true,
  width = 1080,
  height = 1920,
  fontSize = 26,
}: RequestFlowProps) {
  if (waypoints.length === 0) return null;
  const elapsed = now - start;
  if (elapsed < 0) return null;

  const last = waypoints.length - 1;
  const idx = Math.min(last, Math.floor(elapsed / Math.max(0.001, hop)));
  const u = clamp01((elapsed - idx * hop) / Math.max(0.001, hop));
  const a = waypoints[idx];
  const b = waypoints[Math.min(idx + 1, last)];
  const e = easeIO(u);
  const px = lerp(a.x, b.x, e);
  const py = lerp(a.y, b.y, e) - Math.sin(e * Math.PI) * arc;
  const settled = idx === last && u > 0.75;

  return (
    <>
      {trail && (
        <svg width={width} height={height} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none', zIndex: 380}}>
          {idx > 0 && (
            <polyline
              points={waypoints.slice(0, idx + 1).map((w) => `${w.x},${w.y}`).join(' ')}
              fill="none"
              stroke={tone}
              strokeWidth={3}
              strokeDasharray="9 7"
              opacity={0.5}
            />
          )}
          <line x1={a.x} y1={a.y} x2={px} y2={py} stroke={tone} strokeWidth={3} opacity={0.8} />
        </svg>
      )}
      <div style={{position: 'absolute', left: px, top: py, transform: 'translate(-50%,-50%)', zIndex: 400}}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: settled ? '#12161b' : '#ffffff',
            border: `2px solid ${tone}`,
            borderRadius: 12,
            padding: '7px 16px',
            boxShadow: `0 10px 26px rgba(20,26,36,0.28), 0 0 0 ${settled ? 4 : 0}px ${tone}22`,
            whiteSpace: 'nowrap',
          }}
        >
          <span style={{width: 10, height: 10, borderRadius: 5, background: tone}} />
          <span style={{fontSize, fontWeight: 900, fontFamily: "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace", color: settled ? '#ffffff' : '#12161b'}}>
            {a.label}
          </span>
        </div>
      </div>
    </>
  );
}
