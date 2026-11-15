import assert from 'node:assert/strict';
import {test} from 'node:test';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Presenter2D, samplePresenterPose} from '../dist/presenter2d.js';

test('gestures blend from the current pose when a new cue interrupts a gesture', () => {
  const point = {frame: 8, gesture: 'point-left', transitionFrames: 10};
  const explain = {frame: 13, gesture: 'explain', transitionFrames: 8};
  assert.equal(samplePresenterPose([point], 7).left.hand, 'rest');
  assert.equal(samplePresenterPose([point], 18).left.hand, 'point');
  assert.deepEqual(samplePresenterPose([point, explain], 13), samplePresenterPose([point], 13));
  const midpoint = samplePresenterPose([point, explain], 17);
  assert.ok(midpoint.right.wrist[0] > 119 && midpoint.right.wrist[0] < 175);
  assert.equal(samplePresenterPose([point, explain], 21).right.hand, 'open');
  assert.equal(samplePresenterPose([{frame: 0, gesture: 'two', transitionFrames: 0}], 0).right.hand, 'two');
});

test('reusable rigs isolate their SVG IDs and drive blink and mouth separately', () => {
  const face = ({eyeOpen, mouthOpen}) => React.createElement('g', {'data-eye': eyeOpen, 'data-mouth': mouthOpen});
  const markup = renderToStaticMarkup(React.createElement('svg', null,
    React.createElement(Presenter2D, {frame: 5, face, blinkFrames: [5], speech: .65}),
    React.createElement(Presenter2D, {frame: 5, face, speech: .65, mouthOpen: 0}),
  ));
  const ids = Array.from(markup.matchAll(/<linearGradient id="([^"]+)"/g), match => match[1]);
  assert.equal(ids.length, 4);
  assert.equal(new Set(ids).size, 4);
  for (const id of ids) assert.ok(markup.includes(`url(#${id})`));
  assert.match(markup, /data-eye="0\.04" data-mouth="0\.65"/);
  assert.match(markup, /data-eye="1" data-mouth="0"/);
});
