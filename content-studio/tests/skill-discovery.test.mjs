import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {discoverSkills} from '../scripts/skill-discovery.mjs';
import {installSkills, retireManagedSkillLinks} from '../scripts/install-skills.mjs';

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
  const stock = path.join(result.release, 'content-studio', 'skills', 'content-studio-video', 'stock-library', 'assets');
  // A managed install can include owned CTA stock, but never local-only Reel excerpts.
  assert.ok(fs.existsSync(path.join(stock, 'media', 'cta')));
  assert.equal(fs.existsSync(path.join(stock, 'media', 'sfx')), false);
  for (const {name, folder} of source) {
    assert.equal(fs.realpathSync(path.join(root, 'skills', name)).toLowerCase(), fs.realpathSync(folder).toLowerCase());
  }
  const name = source[0].name;
  fs.unlinkSync(path.join(root, 'skills', name));
  fs.mkdirSync(path.join(root, 'skills', name));
  assert.throws(() => installSkills({target: root, dependencies: false}), /Refusing to replace unmanaged skill/);
});

test('reinstall retires managed migration links and preserves user-owned folders', (t) => {
  const root = scratch(t);
  let result;
  try {
    result = installSkills({target: root, dependencies: false});
  } catch (error) {
    if (process.platform === 'win32' && error.code === 'EPERM') {
      t.skip('junction creation denied by sandbox');
      return;
    }
    throw error;
  }
  const skills = path.join(root, 'skills');
  const nested = path.join(result.release, 'content-studio', 'skills', 'content-studio-video');
  const managed = ['content-studio-videogen', 'content-studio-videopreprocess'];
  for (const name of managed) {
    fs.symlinkSync(nested, path.join(skills, name), process.platform === 'win32' ? 'junction' : 'dir');
  }
  const unmanaged = path.join(skills, 'content-studio-videoedit');
  fs.mkdirSync(unmanaged);
  fs.writeFileSync(path.join(unmanaged, 'owner.txt'), 'keep');

  const updated = installSkills({target: root, dependencies: false});
  for (const name of managed) {
    assert.equal(fs.existsSync(path.join(skills, name)), false);
    assert.ok(updated.removed.includes(path.join(skills, name)));
  }
  assert.equal(fs.readFileSync(path.join(unmanaged, 'owner.txt'), 'utf8'), 'keep');
  assert.equal(updated.removed.includes(unmanaged), false);
});

test('retirement cleanup unlinks all three managed aliases and leaves external or owned entries', () => {
  const parent = path.join('C:', 'agents');
  const base = path.join(parent, 'skills');
  const managedRoot = path.join(parent, 'content-studio', 'v0.6.1');
  const entries = new Map([
    ['content-studio-videogen', {link: true, target: path.join(managedRoot, 'videogen')}],
    ['content-studio-videopreprocess', {link: true, target: path.join(managedRoot, 'preprocess')}],
    ['content-studio-videoedit', {link: true, target: path.join(managedRoot, 'clip-edit')}],
  ].map(([name, value]) => [path.join(base, name), value]));
  const removed = [];
  const io = {
    existsSync: (candidate) => entries.has(candidate),
    lstatSync: (candidate) => ({isSymbolicLink: () => entries.get(candidate).link}),
    realpathSync: (candidate) => entries.get(candidate).target,
    unlinkSync: (candidate) => { removed.push(candidate); entries.delete(candidate); },
  };
  assert.deepEqual(retireManagedSkillLinks({parent, bases: [base], io}), removed);
  assert.equal(removed.length, 3);

  entries.set(path.join(base, 'content-studio-videoedit'), {link: false});
  entries.set(path.join(base, 'content-studio-videogen'), {link: true, target: path.join(parent, 'other', 'videogen')});
  assert.deepEqual(retireManagedSkillLinks({parent, bases: [base], io}), []);
  assert.equal(entries.size, 2);
});
