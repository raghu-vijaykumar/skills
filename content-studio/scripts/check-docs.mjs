// Check maintained Content Studio links and direct skill discovery before release.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {discoverSkills} from './skill-discovery.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','..');
const bundle=path.join(root,'content-studio');
const skillRoot=path.join(bundle,'skills');
const files=[path.join(root,'README.md'),path.join(root,'AGENTS.md'),
  path.join(bundle,'README.md'),path.join(bundle,'PROPOSED_FOLDER_STRUCTURE.md'),
  ...fs.readdirSync(path.join(bundle,'prompts')).filter((file)=>file.endsWith('.md')).map((file)=>path.join(bundle,'prompts',file))];
const entries=discoverSkills(skillRoot);
for(const {folder,entry} of entries) {
  files.push(entry);
  const localReadme=path.join(folder,'README.md');
  if(fs.existsSync(localReadme)) files.push(localReadme);
  const references=path.join(folder,'references');
  if(fs.existsSync(references)) files.push(...fs.readdirSync(references).filter((file)=>file.endsWith('.md')).map((file)=>path.join(references,file)));
}
let links=0;
for(const file of files) {
  const text=fs.readFileSync(file,'utf8');
  for(const match of text.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
    const ref=match[1].split('#')[0];
    if(!ref || /^(?:https?:|mailto:|<)/.test(ref)) continue;
    const target=path.resolve(path.dirname(file),decodeURIComponent(ref));
    if(!fs.existsSync(target)) throw new Error(`${path.relative(root,file)}: broken link ${ref}`);
    links++;
  }
}
console.log(`Docs: ${files.length} maintained files, ${links} local links, ${entries.length} unique skills`);
