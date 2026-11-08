import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {discoverSkills} from '../scripts/skill-discovery.mjs';
import {installSkills} from '../scripts/install-skills.mjs';

function scratch(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'content-studio-skills-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  return root;
}

test('nested skills are discovered by their unique frontmatter names', (t) => {
  const root = scratch(t);
  for (const [folder, name] of [['router', 'content-studio-video'], ['router/source/ingest', 'content-studio-video-ingest']]) {
    const skill = path.join(root, folder);
    fs.mkdirSync(skill, {recursive: true});
    fs.writeFileSync(path.join(skill, 'SKILL.md'), `---\nname: ${name}\ndescription: Test ${name}.\n---\n`);
  }
  assert.deepEqual(discoverSkills(root).map(({name}) => name), ['content-studio-video', 'content-studio-video-ingest']);
  const duplicate = path.join(root, 'other');
  fs.mkdirSync(duplicate);
  fs.writeFileSync(path.join(duplicate, 'SKILL.md'), '---\nname: content-studio-video\ndescription: Duplicate.\n---\n');
  assert.throws(() => discoverSkills(root), /Duplicate skill name/);
});

test('supported methods need a real local script', (t) => {
  const root = scratch(t);
  const folder = path.join(root, 'upscale');
  fs.mkdirSync(folder);
  fs.writeFileSync(path.join(folder, 'SKILL.md'),
    '---\nname: content-studio-video-upscale\ndescription: Upscale a completed edit.\n---\n');
  fs.writeFileSync(path.join(folder, 'methods.json'), JSON.stringify({methods: [
    {id: 'lanczos', status: 'supported', script: 'scripts/lanczos.py'},
    {id: 'deblur', status: 'unsupported'},
  ]}));
  assert.throws(() => discoverSkills(root), /Missing method script/);
  fs.mkdirSync(path.join(folder, 'scripts'));
  fs.writeFileSync(path.join(folder, 'scripts', 'lanczos.py'), '# test method\n');
  assert.equal(discoverSkills(root)[0].name, 'content-studio-video-upscale');
});

test('managed install links nested skills directly and refuses unmanaged destinations', (t) => {
  const root = scratch(t);
  let result;
  try {
    result = installSkills({target: root, dependencies: false});
  } catch (error) {
    // Windows sandbox profiles can deny junction creation even in a temporary folder.
    if (process.platform === 'win32' && error.code === 'EPERM') {
      t.skip('junction creation denied by sandbox');
      return;
    }
    throw error;
  }
  const source = discoverSkills(path.join(result.release, 'content-studio', 'skills'));
  assert.equal(result.skills.length, source.length);
  for (const {name, folder} of source) {
    assert.equal(fs.realpathSync(path.join(root, 'skills', name)).toLowerCase(), fs.realpathSync(folder).toLowerCase());
  }
  const name = source[0].name;
  fs.unlinkSync(path.join(root, 'skills', name));
  fs.mkdirSync(path.join(root, 'skills', name));
  assert.throws(() => installSkills({target: root, dependencies: false}), /Refusing to replace unmanaged skill/);
});
