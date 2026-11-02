#!/usr/bin/env node
// Read the shipped registries so a new built-in appears without editing this skill.
import {builtInStyles} from '../../content-studio-videogen/dist/styles.js';
import {CONTENT_STYLES} from '../../content-studio-videogen/dist/design/contentStyles.mjs';
import {neutralTheme, reviseLabsTheme} from '../../content-studio-videogen/dist/themes.js';

const flags=new Set(process.argv.slice(2));
if ([...flags].some((flag)=>!['--json','--themes'].includes(flag))) {
  console.error('Usage: node list.mjs [--json] [--themes]');
  process.exit(2);
}
const styles=builtInStyles.map((style)=>({
  id:style.id,
  name:style.name,
  formats:[...style.formats],
  use:CONTENT_STYLES.find((item)=>item.id===style.id)?.use ??
    (style.id==='hairline' ? 'Narration-timed, frame-deterministic line-art animation' : ''),
  requiresFirsthandEvidence:Boolean(style.requiresFirsthandEvidence),
}));
const themes=[neutralTheme,reviseLabsTheme].map((theme)=>({id:theme.id,brand:theme.brand}));
const items=flags.has('--themes') ? themes : styles;
if (flags.has('--json')) console.log(JSON.stringify(items,null,2));
else {
  console.log(flags.has('--themes') ? 'Built-in themes' : 'Built-in styles');
  for(const item of items) console.log(flags.has('--themes') ?
    `${item.id}: ${item.brand || 'unbranded'}` :
    `${item.id}: ${item.name} (${item.formats.join(', ')}) — ${item.use}${item.requiresFirsthandEvidence ? '; requires firsthand evidence' : ''}`);
}
