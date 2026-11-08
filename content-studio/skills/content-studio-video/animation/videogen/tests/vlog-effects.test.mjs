import assert from 'node:assert/strict';
import test from 'node:test';
import {
  VlogEffect,
  VlogTransition,
  midPeak,
  swipeOffset,
  vlogProgress,
} from '@raghu-vijaykumar/videogen/runtime/vlogEffects';

test('vlog effects are exported for consuming Remotion projects', () => {
  assert.equal(typeof VlogEffect, 'function');
  assert.equal(typeof VlogTransition, 'function');
});

test('a transition reaches both endpoints exactly and peaks at its midpoint', () => {
  assert.equal(vlogProgress(0, 11), 0);
  assert.equal(vlogProgress(5, 11), 0.5);
  assert.equal(vlogProgress(10, 11), 1);
  assert.equal(midPeak(vlogProgress(5, 11)), 1);
  assert.equal(midPeak(0.45), 1);
  assert.equal(midPeak(0.55), 1);
  assert.equal(swipeOffset(0), -100);
  assert.equal(swipeOffset(0.5), 0);
  assert.equal(swipeOffset(1), 100);
  assert.equal(midPeak(vlogProgress(0, 11)), 0);
  assert.equal(midPeak(vlogProgress(10, 11)), 0);
  assert.throws(() => vlogProgress(0, 1), /at least 2/);
});
