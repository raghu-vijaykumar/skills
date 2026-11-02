// Check maintained Content Studio links and direct skill discovery before release.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','..');
const bundle=path.join(root,'content-studio');
const skillRoot=path.join(bundle,'skills');
const names=['content-studio','content-studio-ideagen','content-studio-styles','content-studio-videogen',
  'content-studio-videopreprocess','content-studio-videoedit','content-studio-publish','content-studio-archive'];
const files=[path.join(root,'README.md'),path.join(bundle,'README.md')];
for(const name of names) {
  const folder=path.join(skillRoot,name);
  const entry=path.join(folder,'SKILL.md');
  if(!fs.existsSync(entry)) throw new Error(`Missing skill: ${name}`);
  const text=fs.readFileSync(entry,'utf8');
  if(!text.startsWith(`---\nname: ${name}\n`) && !text.startsWith(`---\r\nname: ${name}\r\n`))
    throw new Error(`Skill frontmatter mismatch: ${name}`);
  files.push(entry);
  const references=path.join(folder,'references');
  if(fs.existsSync(references)) files.push(...fs.readdirSync(references).filter((file)=>file.endsWith('.md')).map((file)=>path.join(references,file)));
}
const discovered=[];
function walk(folder) {
  for(const item of fs.readdirSync(folder,{withFileTypes:true})) {
    const file=path.join(folder,item.name);
    if(item.isDirectory()) walk(file);
    else if(item.name==='SKILL.md') discovered.push(file);
  }
}
walk(bundle);
if(discovered.length!==names.length) throw new Error(`Expected eight discoverable skills, found ${discovered.length}`);
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
console.log(`Docs: ${files.length} maintained files, ${links} local links, eight unique skills`);
