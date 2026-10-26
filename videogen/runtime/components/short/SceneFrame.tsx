import React from 'react';
import {FONT_SANS} from '../../design/typography.ts';

// Shared scene shell: applies the house font and clips overflow. The background
// stays transparent so the composition's own background shows through.
export function SceneFrame({children, background = 'transparent'}: {children: React.ReactNode; background?: string}) {
  return (
    <div style={{position: 'absolute', inset: 0, background, fontFamily: FONT_SANS, overflow: 'hidden'}}>{children}</div>
  );
}
