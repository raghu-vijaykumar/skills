import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';

const cli = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'cli.mjs');

test('sync-skill uses the nested skill name and removes only managed old copies', (t) => {
  const project = fs.mkdtempSync(path.join(os.tmpdir(), 'videogen-sync-skill-'));
  t.after(() => fs.rmSync(project, {recursive: true, force: true}));
  const skills = path.join(project, '.agents', 'skills');
  const retired = path.join(skills, 'content-studio-videogen');
  const current = path.join(skills, 'content-studio-video-videogen');
  fs.mkdirSync(retired, {recursive: true});
  fs.writeFileSync(path.join(retired, '.videogen-version'), 'old\n');

  const run = () => spawnSync(process.execPath, [cli, 'sync-skill'], {cwd: project, encoding: 'utf8'});
  const first = run();
  assert.equal(first.status, 0, first.stderr);
  assert.equal(fs.existsSync(retired), false);
  assert.ok(fs.existsSync(path.join(current, '.videogen-version')));
  assert.match(fs.readFileSync(path.join(current, 'SKILL.md'), 'utf8'), /name: content-studio-video-videogen/);

  // An old skill without the sync marker belongs to the project and survives another sync.
  fs.mkdirSync(retired);
  fs.writeFileSync(path.join(retired, 'owner.txt'), 'keep');
  const second = run();
  assert.equal(second.status, 0, second.stderr);
  assert.equal(fs.readFileSync(path.join(retired, 'owner.txt'), 'utf8'), 'keep');
});
