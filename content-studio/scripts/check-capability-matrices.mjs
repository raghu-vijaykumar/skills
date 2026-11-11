// Verify every video capability matrix against its skill manifest, evidence, and presets.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {discoverSkills} from './skill-discovery.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const videoRoot = path.join(root, 'content-studio', 'skills', 'content-studio-video');
const expectedUnsupported = new Set([
  'edit/color/lut',
  'edit/reflection/generative-removal',
  'edit/restoration/deblur',
  'timeline/upscale-real-esrgan',
  'timeline/upscale-pytorch',
  'timeline/hdr-dolby-vision',
]);
// Reel SFX adds two real methods and one leaf matrix.
const expectedMethodCount = 113;
const expectedMatrixCount = 43;

const skills = discoverSkills(path.join(root, 'content-studio', 'skills'))
  .filter(({folder}) => folder === videoRoot || folder.startsWith(videoRoot + path.sep));
const folders = skills.map(({folder}) => folder);
const hasChildSkill = (folder) => folders.some((other) => other.startsWith(folder + path.sep));

const readManifest = (folder) => {
  const file = path.join(folder, 'methods.json');
  if (!fs.existsSync(file)) return null;
  const manifest = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!Array.isArray(manifest.methods)) throw new Error(`Invalid method registry: ${file}`);
  return manifest.methods;
};

// Leaves always need a matrix. A parent skill also needs one when it owns methods.
const targets = folders
  .filter((folder) => {
    if (!hasChildSkill(folder)) return true;
    return (readManifest(folder) ?? []).length > 0;
  })
  .sort();

if (targets.length !== expectedMatrixCount)
  throw new Error(`Expected ${expectedMatrixCount} video capability matrices, found ${targets.length}`);

const rowPattern = /^\|\s*`([^`]+)`\s*\|\s*(Supported|Unsupported)\s*\|/;
// Picture comparisons must expose temporal behavior, even for effects that
// look spatial at one frame. Static diagnostic masks remain separate evidence.
const requiredGifRows = new Map([
  ['edit/color', ['preset', 'shot-match']],
  ['edit/reflection', ['fix', 'preview', 'ai']],
  ['edit/reframe', ['subjects', 'saliency', 'center']],
  ['edit/restoration', ['denoise-light', 'denoise-medium', 'denoise-nlmeans',
    'deflicker', 'lens', 'sharpen-light', 'sharpen-medium']],
  ['edit/upscale', ['compare', 'lanczos', 'real-esrgan', 'pytorch']],
  ['source/blur-review', ['approved-cuts']],
  ['source/stabilize', ['vidstab']],
  ['timeline', ['crop', 'lens-correction', 'denoise-light', 'denoise-medium',
    'deflicker', 'upscale-lanczos', 'color-eq', 'sharpen-light',
    'sharpen-medium', 'title', 'motion-graphics-ass']],
].map(([folder, ids]) => [folder, new Set(ids)]));
let methodCount = 0;
const unsupported = new Set();

function section(text, heading) {
  const start = text.indexOf(`## ${heading}`);
  if (start < 0) return '';
  const rest = text.slice(start + heading.length + 3);
  const end = rest.search(/^## /m);
  return end < 0 ? rest : rest.slice(0, end);
}

function checkEvidence(rel, id, row) {
  const cells = row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|');
  if (cells.length !== 6)
    throw new Error(`${rel}: ${id} matrix row must have 6 columns, found ${cells.length}`);
  const links = [...cells[4].matchAll(/\[[^\]]+\]\(([^)]+)\)/g)].map((match) => match[1]);
  if (!links.length) throw new Error(`${rel}: ${id} has no evidence link`);
  const videoArea = /^(?:edit|source|timeline)(?:\/|$)/.test(rel.replaceAll('\\', '/'));
  const saysBeforeAfter = /before\s*(?:\/|and|-)\s*after/i.test(cells[4]);
  if ((requiredGifRows.get(rel.replaceAll('\\', '/'))?.has(id) ||
       (videoArea && saysBeforeAfter)) &&
      !links.some((link) => /\.gif(?:#.*)?$/i.test(link)))
    throw new Error(`${rel}: ${id} must link a moving before/after GIF`);
  for (const link of links) {
    const ref = link.split('#')[0];
    if (!ref) continue;
    if (/^(?:https?:|mailto:|<)/.test(ref)) throw new Error(`${rel}: ${id} evidence must be local: ${link}`);
    const target = path.resolve(path.dirname(path.join(videoRoot, rel, 'README.md')), decodeURIComponent(ref));
    if (!fs.existsSync(target)) throw new Error(`${rel}: ${id} missing evidence ${link}`);
  }
}

for (const folder of targets) {
  const rel = path.relative(videoRoot, folder);
  const readme = path.join(folder, 'README.md');
  if (!fs.existsSync(readme)) throw new Error(`${rel}: missing README.md capability matrix`);
  const text = fs.readFileSync(readme, 'utf8');
  const rows = section(text, 'Capability matrix')
    .split(/\r?\n/)
    .filter((line) => rowPattern.test(line.trim()));
  if (!rows.length) throw new Error(`${rel}: empty capability matrix`);

  const seen = new Map();
  for (const line of rows) {
    const match = line.trim().match(rowPattern);
    const id = match[1];
    const status = match[2];
    if (seen.has(id)) throw new Error(`${rel}: duplicate capability row ${id}`);
    seen.set(id, status);
    checkEvidence(rel, id, line);
  }

  const methods = readManifest(folder);
  if (methods === null) {
    if (!text.includes('This leaf has no `methods.json` manifest'))
      throw new Error(`${rel}: README must label its documented workflow capabilities`);
    continue;
  }
  if (!methods.length) {
    if (!text.includes('This leaf has an empty `methods.json` manifest'))
      throw new Error(`${rel}: README must explain the empty manifest`);
    continue;
  }

  methodCount += methods.length;
  const manifestIds = new Set(methods.map((method) => method.id));
  for (const id of manifestIds)
    if (!seen.has(id)) throw new Error(`${rel}: manifest method ${id} is missing from the matrix`);
  for (const id of seen.keys())
    if (!manifestIds.has(id)) throw new Error(`${rel}: matrix row ${id} is not a manifest method`);
  for (const method of methods) {
    const expected = method.status === 'supported' ? 'Supported' : 'Unsupported';
    if (seen.get(method.id) !== expected)
      throw new Error(`${rel}: ${method.id} is ${seen.get(method.id)}, manifest says ${expected}`);
    if (method.status === 'unsupported') unsupported.add(`${rel}/${method.id}`.replaceAll('\\', '/'));
  }
}

if (methodCount !== expectedMethodCount)
  throw new Error(`Expected ${expectedMethodCount} declared methods, covered ${methodCount}`);
if (unsupported.size !== expectedUnsupported.size ||
    [...expectedUnsupported].some((id) => !unsupported.has(id)))
  throw new Error(`Unsupported methods changed: ${[...unsupported].sort().join(', ')}`);

// Named transition variants must match both the registry and the visual gallery.
const transitionsFolder = path.join(videoRoot, 'edit', 'transitions');
const transitions = JSON.parse(
  fs.readFileSync(path.join(transitionsFolder, 'presets', 'transitions.json'), 'utf8'),
).transitions;
const transitionText = fs.readFileSync(path.join(transitionsFolder, 'README.md'), 'utf8');
const gallery = new Set(
  [...transitionText.matchAll(/^\|\s*\[`([^`]+)`\]\(scripts\//gm)].map((match) => match[1]),
);
const registryIds = new Set(transitions.map((transition) => transition.id));
for (const id of registryIds)
  if (!gallery.has(id)) throw new Error(`transitions: ${id} is missing from the visual gallery`);
for (const id of gallery)
  if (!registryIds.has(id)) throw new Error(`transitions: ${id} is not in presets/transitions.json`);

// Motion-graphics presets and effect names must be documented.
const graphicsFolder = path.join(videoRoot, 'edit', 'motion-graphics');
const graphics = JSON.parse(
  fs.readFileSync(path.join(graphicsFolder, 'presets', 'presets.json'), 'utf8'),
).presets;
const graphicsText = fs.readFileSync(path.join(graphicsFolder, 'README.md'), 'utf8');
for (const id of Object.keys(graphics))
  if (!graphicsText.includes(`\`${id}\``)) throw new Error(`motion-graphics: preset ${id} is undocumented`);
const overlay = fs.readFileSync(path.join(graphicsFolder, 'scripts', 'overlay.py'), 'utf8');
const effects = overlay.match(/preset[^\n]*\{([^}]+)\}/)?.[1];
if (!effects) throw new Error('motion-graphics: cannot read effect presets from overlay.py');
for (const id of [...effects.matchAll(/"([^"]+)"/g)].map((match) => match[1]))
  if (!graphicsText.includes(`\`${id}\``)) throw new Error(`motion-graphics: effect ${id} is undocumented`);

// Meme profiles and insertion modes must be documented.
const memesFolder = path.join(videoRoot, 'memes');
const memesText = fs.readFileSync(path.join(memesFolder, 'README.md'), 'utf8');
for (const file of fs.readdirSync(path.join(memesFolder, 'presets')).filter((name) => name.endsWith('.json'))) {
  const profile = JSON.parse(fs.readFileSync(path.join(memesFolder, 'presets', file), 'utf8'));
  if (!memesText.includes(`\`${profile.category}\``) && !memesText.includes(`[${profile.category}]`))
    throw new Error(`memes: profile ${profile.category} is undocumented`);
  for (const mode of profile.modes)
    if (!memesText.includes(`\`${mode}\``)) throw new Error(`memes: mode ${mode} is undocumented`);
}

console.log(
  `Capability matrices: ${targets.length} skills, ${methodCount} methods, ` +
  `${unsupported.size} unsupported, ${transitions.length} transitions, ` +
  `${Object.keys(graphics).length} presets`,
);
