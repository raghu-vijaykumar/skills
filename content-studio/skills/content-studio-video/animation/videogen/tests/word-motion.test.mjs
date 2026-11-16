import assert from 'node:assert/strict';
import {test} from 'node:test';
import {sampleWordMotion} from '../dist/components/motion-lab/index.js';

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
