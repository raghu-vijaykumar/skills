import React from 'react';
import {CYAN, TEXT} from '../../design/color.ts';
import {FONT_SANS, LINE_HEIGHT, TRACKING, TYPE, WEIGHT} from '../../design/typography.ts';
import {BAND} from '../../design/surfaces.ts';

// Shared scene title: kicker + one-line title, pinned to the top title band.
// Every short renders this so the 52/26 hierarchy is consistent by construction.
export function Title({children, kicker}: {children: React.ReactNode; kicker?: string}) {
  return (
    <div style={{position: 'absolute', top: BAND.titleTop, left: BAND.titleSide, right: BAND.titleSide, fontFamily: FONT_SANS}}>
      {kicker && (
        <div
          style={{
            fontSize: TYPE.kicker,
            letterSpacing: TRACKING.kicker,
            color: CYAN,
            fontWeight: WEIGHT.bold,
            marginBottom: 12,
          }}
        >
          {kicker.toUpperCase()}
        </div>
      )}
      <div style={{fontSize: TYPE.title, lineHeight: LINE_HEIGHT.title, color: TEXT, fontWeight: WEIGHT.extraBold}}>{children}</div>
    </div>
  );
}
