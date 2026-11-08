import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync, spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';

const cli = fileURLToPath(new URL('../scripts/cli.mjs', import.meta.url));
const tempRoot = path.resolve('tmp');
fs.mkdirSync(tempRoot, {recursive: true});

test('CLI exposes YouTube now, Instagram now, and native YouTube scheduling as dry runs', () => {
  const root = fs.mkdtempSync(path.join(tempRoot, 'videogen-publish-cli-'));
  const draft = path.join(root, 'drafts', '001-test');
  try {
    fs.mkdirSync(path.join(draft, 'content'), {recursive: true});
    fs.writeFileSync(path.join(root, 'videogen.config.ts'), "export default {entryPoint:'src/entry.tsx', videosDir:'drafts', contentDir:'content', theme:{}, styles:[]};\n");
    fs.writeFileSync(path.join(draft, 'content', 'video.yaml'), 'video:\n  id: 001-test\n  compositionId: Test\n  title: Exact title\npublishing:\n  youtube:\n    title: Exact title\n    description: Exact description\n  instagram:\n    caption: Reel caption\n');
    fs.writeFileSync(path.join(draft, 'video.mp4'), 'render');
    fs.writeFileSync(path.join(draft, 'thumbnail.jpg'), 'thumbnail');
    fs.writeFileSync(path.join(draft, 'title.txt'), 'Exact title\n');
    fs.writeFileSync(path.join(draft, 'description.txt'), 'Exact description\n');
    const invoke = (...args) => spawnSync(process.execPath, [cli, 'publish', '001-test', ...args], {cwd: root, encoding: 'utf8'});
    const youtube = invoke();
    assert.equal(youtube.status, 0, youtube.stderr);
    assert.equal(JSON.parse(youtube.stdout).dryRun, true);
    const instagram = invoke('--platform', 'instagram');
    assert.equal(instagram.status, 0, instagram.stderr);
    assert.equal(JSON.parse(instagram.stdout).platform, 'instagram');
    const scheduled = invoke('--at', '2030-12-01T18:00:00+05:30');
    assert.equal(scheduled.status, 0, scheduled.stderr);
    assert.equal(JSON.parse(scheduled.stdout).publishAt, '2030-12-01T12:30:00.000Z');
    assert.notEqual(invoke('--platform', 'instagram', '--at', '2030-12-01T18:00:00+05:30').status, 0);
    assert.notEqual(invoke('--platform', 'other').status, 0);
    assert.equal(fs.existsSync(path.join(draft, 'draft.json')), false);
  } finally {
    const resolved = path.resolve(root);
    if (!resolved.startsWith(tempRoot + path.sep)) throw new Error(`Unsafe test cleanup: ${resolved}`);
    fs.rmSync(resolved, {recursive: true, force: true});
  }
});
