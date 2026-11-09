import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

test('every video capability matrix matches its manifest, evidence, and presets', () => {
  const script = path.join(root, 'content-studio', 'scripts', 'check-capability-matrices.mjs');
  const result = spawnSync(process.execPath, [script], {encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Capability matrices: 41 skills, 109 methods, 6 unsupported/);
});
