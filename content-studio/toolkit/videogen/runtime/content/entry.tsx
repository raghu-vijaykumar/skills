import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {ContentCard, type CardProps} from './ContentCard.tsx';

const defaults: CardProps = {style: 'core-explainer', kind: 'text', heading: 'A clear question', body: 'Show the answer with actual evidence.', width: 1080, height: 1350, durationSeconds: 1};

function ContentRoot() {
  return <Composition
    id="ContentCard"
    component={ContentCard}
    width={1080}
    height={1350}
    fps={30}
    durationInFrames={30}
    defaultProps={defaults}
    calculateMetadata={({props}) => ({width: props.width ?? 1080, height: props.height ?? 1350, durationInFrames: Math.max(1, Math.ceil((props.durationSeconds ?? 1) * 30))})}
  />;
}

registerRoot(ContentRoot);
