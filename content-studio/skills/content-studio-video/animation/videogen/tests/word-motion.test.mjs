import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {compileWordChoreography, sampleWordMotion, WordMotionCast} from '../dist/components/motion-lab/index.js';

test('word cues change on their exact onset and hold through pauses', () => {
  const cues = [
    {startFrame: 11, endFrame: 15, text: 'Press', line: 0, actor: 'keycap', action: 'descend'},
    {startFrame: 18, endFrame: 25, text: 'now', line: 0, actor: 'contact', action: 'close'},
  ];

  assert.equal(sampleWordMotion(cues, 10).index, -1);
  assert.deepEqual(sampleWordMotion(cues, 11), {cue: cues[0], index: 0, elapsed: 0, speaking: true});
  assert.deepEqual(sampleWordMotion(cues, 16), {cue: cues[0], index: 0, elapsed: 5, speaking: false});
  assert.deepEqual(sampleWordMotion(cues, 18), {cue: cues[1], index: 1, elapsed: 0, speaking: true});
});

const cues = [
  {startFrame: 2, endFrame: 5, text: 'Press', line: 0, actor: 'switch', action: 'down'},
  {startFrame: 6, endFrame: 9, text: 'contact', line: 0, actor: 'switch', action: 'connect'},
  {startFrame: 10, endFrame: 13, text: 'release', line: 0, actor: 'switch', action: 'up'},
];
const actors = {
  switch: {initial: {travel: 0, signal: 0}, actions: {
    down: {travel: {to: 20, frames: 10}},
    connect: {signal: {to: 1, frames: 8, ease: 'smooth'}},
    up: {travel: {to: 0, frames: 4, ease: 'smooth'}},
  }},
};

test('word actions interrupt only the named channels and hold state after a phrase', () => {
  const scene = compileWordChoreography(cues, actors);
  assert.deepEqual(scene.sample('switch', 100), {travel: 0, signal: 1});
  assert.deepEqual(scene.sample('switch', 0), {travel: 0, signal: 0});
  assert.deepEqual(scene.sample('switch', 7), {travel: 10, signal: 0.04296875});
  assert.deepEqual(scene.sample('switch', 10), {travel: 16, signal: 0.5});
  assert.deepEqual(scene.sample('switch', 12), {travel: 8, signal: 0.84375});
});

test('an art swap receives the exact same rig values for every frame', () => {
  const scene = compileWordChoreography(cues, actors);
  const paint = tag => ({channels, frame}) => createElement(tag, {id: `switch-${frame}`, ...channels});
  const render = (frame, art) => renderToStaticMarkup(createElement(WordMotionCast, {choreography: scene, art, frame}));
  for (let frame = 0; frame < 16; frame += 1) {
    const anime = render(frame, {switch: paint('ellipse')});
    const pixelArt = render(frame, {switch: paint('rect')});
    assert.equal(anime.replaceAll('ellipse', 'rect'), pixelArt);
  }
  assert.throws(() => render(0, {}), /Art preset is missing actor switch/);
});

test('word action evidence flags repeated states and tweens that miss their word window', () => {
  const word = (startFrame, action) => ({startFrame, endFrame: startFrame + 1, text: action, line: 0,
    actor: 'clock', action});
  const scene = compileWordChoreography([
    word(0, 'reveal'), word(2, 'reveal'), word(4, 'tick'),
    word(5, 'focus'), word(8, 'ring'),
  ], {
    clock: {initial: {opacity: 0, rotation: 0, bright: 0}, actions: {
      reveal: {opacity: 1},
      tick: {rotation: {to: 30, frames: 4}},
      focus: {bright: 1},
      ring: {rotation: {to: 60, frames: 4, ease: 'smooth'}},
    }},
  });
  assert.deepEqual(scene.inspectWordActions(12).map(row => row.changedChannels),
    [['opacity'], [], [], ['bright'], ['rotation']]);
  assert.equal(scene.sample('clock', 5).rotation, 7.5);
  assert.throws(() => scene.inspectWordActions(8), /exclusive end frame/);
});

test('missing word bindings and invalid track settings fail before rendering', () => {
  assert.throws(() => compileWordChoreography(cues, {}), /Press: missing actor switch/);
  assert.throws(() => compileWordChoreography([{...cues[0], action: 'constructor'}], actors), /missing action/);
  assert.throws(() => compileWordChoreography([cues[1], cues[0]], actors), /ordered word frames/);
  const downWith = target => ({switch: {...actors.switch, actions: {down: target}}});
  assert.throws(() => compileWordChoreography([cues[0]], downWith({pivot: 1})), /missing initial channel/);
  assert.throws(() => compileWordChoreography([cues[0]], downWith({travel: {to: 1, frames: -1}})), /invalid target/);
  assert.equal(compileWordChoreography([cues[0]], downWith({travel: 1})).sample('switch', 2).travel, 1);
});
