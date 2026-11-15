import assert from 'node:assert/strict';
import {test} from 'node:test';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {activeHeadlineCue, ChapterSpine, KineticHeadline, LayeredStack} from '../dist/components/motion-lab/index.js';

const cues = [
  {start: 0, end: 1, lines: [[{text: 'One ', emphasis: false}, {text: 'charge', emphasis: true}]]},
  {start: 1, end: 2, lines: [[{text: 'One ', emphasis: false}, {text: 'result', emphasis: true}]]},
];

test('motion-lab primitives resolve an exact cue boundary and render without reference media', () => {
  assert.equal(activeHeadlineCue(cues, 0.999), cues[0]);
  assert.equal(activeHeadlineCue(cues, 1), cues[1]);
  assert.equal(activeHeadlineCue(cues, 2), undefined);
  const title = renderToStaticMarkup(React.createElement(KineticHeadline, {now: 1, cues}));
  assert.match(title, /result/);
  assert.doesNotMatch(title, /charge/);
  assert.doesNotMatch(title, /opacity:0(?:;|\b)/);
  const spine = renderToStaticMarkup(React.createElement(ChapterSpine, {now: 4, markers: [{label: 'Card', start: 0}, {label: 'Ledger', start: 5}]}));
  assert.match(spine, /Card/);
  assert.match(spine, /Ledger/);
  const waiting = renderToStaticMarkup(React.createElement(ChapterSpine, {now: 0, markers: [{label: 'Card', start: 5}], accent: '#ff00ff'}));
  assert.doesNotMatch(waiting, /color:#ff00ff/);
  const stack = renderToStaticMarkup(React.createElement(LayeredStack, {now: 1, start: 0, layers: [{label: 'Vault'}, {label: 'Ledger'}]}));
  assert.match(stack, /Vault/);
  assert.match(stack, /Ledger/);
});
