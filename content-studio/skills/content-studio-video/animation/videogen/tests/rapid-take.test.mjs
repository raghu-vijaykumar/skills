import assert from 'node:assert/strict';
import test from 'node:test';
import {builtInStyles} from '../dist/styles.js';
import {CONTENT_STYLES} from '../dist/design/contentStyles.mjs';
import {RAPID_TAKE} from '../dist/design/rapidTake.js';
import {RapidStage, Slam, StatSlam, SourceShot, BrowserFrame, MemeCut, Annotation, LowerThird, CutFlash} from '../dist/components/rapid-take/RapidTake.js';

test('rapid-take is a registered video-only style', () => {
  const style = builtInStyles.find((item) => item.id === 'rapid-take');
  assert.ok(style, 'rapid-take must be registered');
  assert.deepEqual([...style.formats], ['video']);
  const editorial = CONTENT_STYLES.find((item) => item.id === 'rapid-take');
  assert.ok(editorial, 'rapid-take must have an editorial description');
  assert.deepEqual([...editorial.formats], ['video']);
  assert.equal(RAPID_TAKE.id, 'rapid-take');
});

test('tech-dispatch no longer advertises video support', () => {
  const style = builtInStyles.find((item) => item.id === 'tech-dispatch');
  assert.ok(style);
  assert.deepEqual([...style.formats], ['carousel', 'post']);
  assert.equal(style.formats.includes('video'), false);
});

test('rapid-take primitives are exported for authored compositions', () => {
  for (const component of [RapidStage, Slam, StatSlam, SourceShot, BrowserFrame, MemeCut, Annotation, LowerThird, CutFlash]) {
    assert.equal(typeof component, 'function');
  }
});
