// Install a version-matched bundle once, then expose its skills as direct children.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

const sourceBundle = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const packageRoot = path.resolve(sourceBundle, '..');
const npmCli = process.env.npm_execpath ?? path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js');
const npmRun = (args) => process.platform === 'win32' ? run(process.execPath, [npmCli, ...args]) : run('npm', args);
const names = ['content-studio','content-studio-ideagen','content-studio-styles','content-studio-videogen',
  'content-studio-videopreprocess','content-studio-videoedit','content-studio-audio','content-studio-autocut','content-studio-music',
  'content-studio-benchmark','content-studio-motion-graphics','content-studio-publish','content-studio-archive',
  'content-studio-memes','content-studio-memory','content-studio-understand','content-studio-voice','content-studio-workflow'];
function run(executable, args) {
  const result = spawnSync(executable, args, {encoding:'utf8', maxBuffer:16*1024*1024});
  if (result.error || result.status !== 0)
    throw new Error(`${executable} failed: ${result.error?.message ?? (result.stderr || result.stdout).trim().split(/\r?\n/).slice(-8).join('\n')}`);
}
export function installSkills({global = false, target = null, dependencies = true} = {}) {
  if (!global && !target) throw new Error('Use --global or --target');
  const parent = path.resolve(target ?? path.join(os.homedir(), '.agents'));
  const version = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8')).version;
  const release = path.join(parent, 'content-studio', `v${version}`);
  const skills = path.join(parent, 'skills');
  const marker = path.join(release, '.content-studio-version');
  fs.mkdirSync(skills, {recursive:true});
  if (!fs.existsSync(release)) {
    fs.mkdirSync(release, {recursive:true});
    fs.cpSync(sourceBundle, path.join(release, 'content-studio'), {recursive:true,
      filter: (item) => {
        const parts = path.relative(sourceBundle, item).split(path.sep);
        if (parts.some((part) => part === 'node_modules' || part === '.local' || part === 'tmp'))
          return false;
        // The local music catalog is private and must not be copied into a release.
        return !(parts.includes('assets') && parts.includes('music') && parts.includes('local'));
      }});
    fs.copyFileSync(path.join(packageRoot, 'package.json'), path.join(release, 'package.json'));
    const lock = path.join(packageRoot, 'package-lock.json');
    const hasLock = fs.existsSync(lock);
    if (hasLock) fs.copyFileSync(lock, path.join(release, 'package-lock.json'));
    if (dependencies) {
      // npm excludes package-lock.json from packed dependencies; use pinned package.json there.
      npmRun([hasLock ? 'ci' : 'install','--prefix',release,'--ignore-scripts']);
      npmRun(['run','build','--prefix',release]);
      npmRun(['ci','--prefix',path.join(release,'content-studio','skills','content-studio-ideagen','digest')]);
    }
    fs.writeFileSync(marker, `${version}\n`);
  } else if (fs.readFileSync(marker,'utf8').trim() !== version) {
    throw new Error(`Unmanaged release folder: ${release}`);
  }
  for (const name of names) {
    const destination = path.join(skills,name);
    const source = path.join(release,'content-studio','skills',name);
    if (!fs.existsSync(path.join(source,'SKILL.md'))) throw new Error(`Missing skill: ${name}`);
    if (fs.existsSync(destination)) {
      const info = fs.lstatSync(destination);
      if (!info.isSymbolicLink()) throw new Error(`Refusing to replace unmanaged skill: ${destination}`);
      const old = fs.realpathSync(destination);
      if (!old.toLowerCase().startsWith(path.join(parent,'content-studio').toLowerCase()+path.sep))
        throw new Error(`Skill link points outside managed releases: ${destination}`);
      fs.unlinkSync(destination);
    }
    fs.symlinkSync(source,destination,process.platform === 'win32' ? 'junction' : 'dir');
  }
  // Both Codex and OpenCode discover these direct children of ~/.agents/skills.
  for (const name of names) {
    const installed = path.join(skills, name);
    const expected = path.join(release, 'content-studio', 'skills', name);
    const actual = fs.realpathSync(installed);
    if (actual.toLowerCase() !== fs.realpathSync(expected).toLowerCase())
      throw new Error(`Skill discovery points at the wrong version: ${name}`);
    const lines = fs.readFileSync(path.join(installed, 'SKILL.md'), 'utf8').split(/\r?\n/);
    if (lines[0] !== '---' || lines[1] !== `name: ${name}`)
      throw new Error(`Skill name/frontmatter mismatch: ${name}`);
  }
  const removed = [];
  if (global) {
    const legacy = ['videogen','content-helper','video-idea-engine','hairline-create','learning-engineer',
      'content-studio-ideas','content-studio-animate','content-studio-vlog'];
    for (const base of [skills, path.join(os.homedir(), '.codex', 'skills'),
      path.join(os.homedir(), '.config', 'opencode', 'skills')]) {
      for (const name of legacy) {
        const candidate = path.join(base, name);
        if (!fs.existsSync(candidate)) continue;
        const absolute = path.resolve(candidate);
        if (!absolute.toLowerCase().startsWith(path.resolve(base).toLowerCase() + path.sep))
          throw new Error(`Unsafe legacy skill path: ${absolute}`);
        const info = fs.lstatSync(absolute);
        // Superseded bundle names may be removed only when they still link to a managed release.
        if (name.startsWith('content-studio-') && (!info.isSymbolicLink() ||
          !fs.realpathSync(absolute).toLowerCase().startsWith(path.join(parent,'content-studio').toLowerCase()+path.sep)))
          throw new Error(`Refusing to remove unmanaged skill: ${absolute}`);
        if (info.isSymbolicLink()) fs.unlinkSync(absolute);
        else if (info.isDirectory() && fs.existsSync(path.join(absolute, 'SKILL.md')))
          fs.rmSync(absolute, {recursive: true, force: true});
        else throw new Error(`Legacy skill is not a managed skill folder: ${absolute}`);
        removed.push(absolute);
      }
    }
  }
  return {version,release,skills:names.map((name) => path.join(skills,name)),removed};
}
