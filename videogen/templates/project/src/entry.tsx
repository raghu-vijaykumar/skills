import React from 'react';
import {Composition, registerRoot} from 'remotion';

const Sample = () => <div style={{width: '100%', height: '100%', background: '#101820', color: 'white', display: 'grid', placeItems: 'center', fontSize: 72}}>Your story</div>;

function Root() {
  return <Composition id="Sample" component={Sample} width={1080} height={1920} fps={30} durationInFrames={150}/>;
}

registerRoot(Root);
