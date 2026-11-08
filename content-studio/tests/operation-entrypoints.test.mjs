import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'skills', 'content-studio-video');

test('individual clip preparation cannot request a joined final', (t) => {
  const script = path.join(root, 'source', 'preprocess', 'scripts', 'prepare_clips.py');
  const result = spawnSync('python', [script, '--final'], {encoding: 'utf8'});
  if (result.error?.code === 'ENOENT') return t.skip('Python unavailable');
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /method option is fixed or unavailable here: --final/);
});

test('finished-edit upscale entrypoint cannot run a draft batch', (t) => {
  const script = path.join(root, 'edit', 'upscale', 'scripts', 'lanczos.py');
  const result = spawnSync('python', [script, '--draft', '123'], {encoding: 'utf8'});
  if (result.error?.code === 'ENOENT') return t.skip('Python unavailable');
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /method option is fixed or unavailable here: --draft/);
});

test('Remotion preview entrypoint requires an explicit bounded range', () => {
  const script = path.join(root, 'animation', 'videogen', 'render', 'scripts', 'preview-range.mjs');
  const result = spawnSync(process.execPath, [script, 'example'], {encoding: 'utf8'});
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /requires --from and --to/);
});
