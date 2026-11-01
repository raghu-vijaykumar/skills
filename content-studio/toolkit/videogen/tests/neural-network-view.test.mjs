import test from 'node:test';
import assert from 'node:assert/strict';
import {NeuralNetwork} from '../dist/components/primitives/NeuralNetworkView.js';
import {buildNetwork} from '../dist/components/primitives/neuralNetwork.js';

// The renderer and state model must survive packaging on case-insensitive filesystems.
test('neural network view and model have distinct package exports', () => {
  assert.equal(typeof NeuralNetwork, 'function');
  assert.equal(typeof buildNetwork, 'function');
});
