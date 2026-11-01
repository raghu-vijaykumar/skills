#!/usr/bin/env node
// Entry point for work shared by edited and code-rendered channel drafts.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {approvePackage, itemFromDraft, verifyPackage} from './package.mjs';
import {transcribeDraft, probeMaster} from './transcribe.mjs';
import {publishYoutube} from '../toolkit/videogen/scripts/publish-youtube.mjs';
import {publishInstagram} from '../toolkit/videogen/scripts/publish-instagram.mjs';
import {installSkills} from './install-skills.mjs';

const bundle = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [command, ...argv] = process.argv.slice(2);
function option(name) {
  const index = argv.indexOf(`--${name}`);
  if (index < 0) return null;
  if (!argv[index + 1] || argv[index + 1].startsWith('--')) throw new Error(`--${name} needs a value`);
  return argv[index + 1];
}
function flag(name) { return argv.includes(`--${name}`); }
function merge(base, override) {
  for (const [key, value] of Object.entries(override)) {
    base[key] = value && typeof value === 'object' && !Array.isArray(value) &&
      base[key] && typeof base[key] === 'object' ? merge(base[key], value) : value;
  }
  return base;
}
function channel() {
  const slug = option('channel');
  if (!slug || !/^[a-z0-9][a-z0-9-]*$/.test(slug)) throw new Error('--channel needs a configured slug');
  const configFile = option('config') ?? path.join(bundle, 'toolkit', 'content-helper', 'config.json');
  const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
  const override = path.join(path.dirname(configFile), 'config.local.json');
  if (fs.existsSync(override)) merge(config, JSON.parse(fs.readFileSync(override, 'utf8')));
  const entry = config.channels?.[slug];
  if (!entry) throw new Error(`Unknown channel: ${slug}`);
  const root = path.resolve(config.workspace, slug);
  const id = option('draft');
  if (!id || !/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(id)) throw new Error('--draft needs a safe folder ID');
  const draft = path.join(root, 'drafts', id);
  if (!fs.statSync(draft, {throwIfNoEntry: false})?.isDirectory()) throw new Error(`Draft not found: ${draft}`);
  return {slug, id, root, draft, entry};
}
function publishingConfig(root, entry) {
  return {workDir: 'analysis', publish: {
    youtube: {clientFile: 'code/secrets/youtube-client.json', tokenFile: 'code/secrets/youtube-token.json',
      ...(entry.publish?.youtube ?? {})},
    instagram: {tokenFile: 'code/secrets/instagram-token.json', ...(entry.publish?.instagram ?? {})}}};
}
function remotionCheck(root, id) {
  const project = path.join(root, 'videogen.config.ts');
  if (!fs.existsSync(project)) throw new Error('Remotion draft needs videogen.config.ts');
  const cli = path.join(bundle, 'toolkit', 'videogen', 'scripts', 'cli.mjs');
  const result = spawnSync(process.execPath, [cli, 'check', id], {cwd: root, encoding: 'utf8'});
  if (result.status !== 0) throw new Error(`Remotion check failed: ${(result.stderr || result.stdout).trim().split(/\r?\n/).slice(-8).join('\n')}`);
}
async function main() {
  if (!command || command === '--help' || command === '-h' || flag('help') || command === 'help') {
    console.log('Usage: content-studio <install-skills|transcribe|approve|publish> [--channel slug --draft id]');
    return;
  }
  if (command === 'install-skills') {
    console.log(JSON.stringify(installSkills({global: flag('global'), target: option('target')}), null, 2));
    return;
  }
  const {id, root, draft, entry} = channel();
  if (command === 'transcribe') {
    console.log(JSON.stringify(transcribeDraft(root, draft, {cli: option('cli'), model: option('model')}), null, 2));
    return;
  }
  if (command === 'approve') {
    console.log(JSON.stringify(approvePackage(draft, id, option('note')), null, 2));
    return;
  }
  if (command === 'publish') {
    const platform = option('platform') ?? 'youtube';
    const at = option('at');
    if (!['youtube','instagram'].includes(platform)) throw new Error('Platform must be youtube or instagram');
    if (platform === 'instagram' && at) throw new Error('Instagram scheduling is not supported');
    const item = itemFromDraft(draft, id);
    if (flag('confirm')) {
      const approved = verifyPackage(draft, id);
      probeMaster(approved.files.master);
      if (item.kind === 'remotion') remotionCheck(root, id);
    }
    process.chdir(root);
    const config = publishingConfig(root, entry);
    const options = {confirm: flag('confirm'), resume: flag('resume'), at};
    const result = platform === 'instagram' ? await publishInstagram(item, config, options) :
      await publishYoutube(item, config, options);
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}
main().catch((error) => { console.error(`content-studio: ${error.message}`); process.exitCode = 1; });
