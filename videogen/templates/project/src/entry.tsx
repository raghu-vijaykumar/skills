import React from 'react';
import {Composition, registerRoot} from 'remotion';
import project from '../videogen.config.ts';

// The starter is a real theme consumer, so both shipped presets and custom
// themes become visible in the first render without changing toolkit code.
const Sample = () => <div style={{width: '100%', height: '100%', background: project.theme.colors.background, color: project.theme.colors.text, fontFamily: project.theme.fonts.sans, display: 'grid', placeItems: 'center', fontSize: 72}}>Your story</div>;

function Root() {
  return <Composition id="Sample" component={Sample} width={1080} height={1920} fps={30} durationInFrames={150}/>;
}

registerRoot(Root);
