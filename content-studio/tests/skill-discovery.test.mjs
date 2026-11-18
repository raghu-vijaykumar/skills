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

test('Social exposes canonical platform operations without compatibility entrypoints', () => {
  // Discovery should surface working skills while hiding routing-only aliases.
  const root = path.resolve('content-studio/skills');
  const names = new Set(discoverSkills(root).map(({name}) => name));
  for (const name of ['content-studio-social',
    'content-studio-social-youtube-publish', 'content-studio-social-youtube-analytics',
    'content-studio-social-linkedin-author', 'content-studio-social-linkedin-publish',
    'content-studio-social-linkedin-analytics', 'content-studio-social-instagram-publish',
    'content-studio-social-instagram-analytics']) {
    assert.ok(names.has(name), `${name} must be independently callable`);
  }
  for (const name of ['content-studio-archive', 'content-studio-audio', 'content-studio-autocut',
    'content-studio-benchmark', 'content-studio-ideagen', 'content-studio-linkedin',
    'content-studio-memes', 'content-studio-memory', 'content-studio-motion-graphics',
    'content-studio-music', 'content-studio-publish', 'content-studio-styles',
    'content-studio-understand', 'content-studio-voice']) {
    assert.equal(names.has(name), false, `${name} is a retired compatibility entrypoint`);
  }
});

test('retired script folders are absent and their canonical helpers remain callable', () => {
  const root = path.resolve('content-studio/skills');
  // These targets used to be hidden behind top-level forwarding scripts.
  const owners = {
    'content-studio-audio': ['audio/mastering/scripts/master.py'],
    'content-studio-autocut': ['edit/autocut/scripts/autocut.py', 'edit/autocut/scripts/timeline.py', 'edit/autocut/agents/openai.yaml'],
    'content-studio-benchmark': ['review/benchmark/scripts/benchmark.py'],
    'content-studio-ideagen': ['planning/ideagen/scripts/plan.py'],
    'content-studio-memes': ['memes/scripts/memes.py'],
    'content-studio-memory': ['memory/scripts/memory.py', 'memory/scripts/compare_kdenlive.py'],
    'content-studio-motion-graphics': ['edit/motion-graphics/scripts/overlay.py', 'edit/motion-graphics/scripts/presets.py'],
    'content-studio-music': ['audio/music/scripts/music.py'],
    'content-studio-styles': ['planning/styles/scripts/list.mjs', 'planning/styles/scripts/style_engine.py', 'animation/engineering-3d/scripts/engineering_blender.py'],
    'content-studio-understand': ['review/understand/scripts/understand.py', 'review/understand/scripts/voiceover.py'],
    'content-studio-voice': ['audio/voice-cloning/scripts/voice.py', 'audio/voice-cloning/scripts/narration.py'],
  };
  for (const [retired, targets] of Object.entries(owners)) {
    assert.equal(fs.existsSync(path.join(root, retired)), false, `${retired} must not be copied into a release`);
    for (const target of targets) assert.ok(fs.existsSync(path.join(root, 'content-studio-video', target)), target);
  }
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
  assert.equal(fs.existsSync(path.join(result.release, 'content-studio', 'skills', 'content-studio-autocut')), false);
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
  const managed = ['content-studio-videogen', 'content-studio-videopreprocess', 'content-studio-linkedin'];
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

test('retirement cleanup unlinks all managed aliases and leaves external or owned entries', () => {
  const parent = path.join('C:', 'agents');
  const base = path.join(parent, 'skills');
  const managedRoot = path.join(parent, 'content-studio', 'v0.6.1');
  const retired = ['content-studio-videogen', 'content-studio-videopreprocess', 'content-studio-videoedit',
    'content-studio-archive', 'content-studio-audio', 'content-studio-autocut',
    'content-studio-benchmark', 'content-studio-ideagen', 'content-studio-linkedin',
    'content-studio-memes', 'content-studio-memory', 'content-studio-motion-graphics',
    'content-studio-music', 'content-studio-publish', 'content-studio-styles',
    'content-studio-understand', 'content-studio-voice'];
  const entries = new Map(retired.map((name) => [path.join(base, name),
    {link: true, target: path.join(managedRoot, name)}]));
  const removed = [];
  const io = {
    existsSync: (candidate) => entries.has(candidate),
    lstatSync: (candidate) => ({isSymbolicLink: () => entries.get(candidate).link}),
    realpathSync: (candidate) => entries.get(candidate).target,
    unlinkSync: (candidate) => { removed.push(candidate); entries.delete(candidate); },
  };
  assert.deepEqual(retireManagedSkillLinks({parent, bases: [base], io}), removed);
  assert.equal(removed.length, retired.length);

  entries.set(path.join(base, 'content-studio-videoedit'), {link: false});
  entries.set(path.join(base, 'content-studio-videogen'), {link: true, target: path.join(parent, 'other', 'videogen')});
  assert.deepEqual(retireManagedSkillLinks({parent, bases: [base], io}), []);
  assert.equal(entries.size, 2);
});
