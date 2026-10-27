// Create only a new video's authored starter files. Existing ideas and briefs survive.
import fs from 'node:fs';
import path from 'node:path';
import {stringify} from 'yaml';

function relativeImport(from, to) {
  let relative = path.relative(path.dirname(from), to).replaceAll('\\', '/');
  if (!relative.startsWith('.')) relative = `./${relative}`;
  return relative;
}

export function scaffoldDraft(config, id, options = {}) {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(id ?? '')) throw new Error('Invalid video ID');
  const cwd = path.resolve(options.cwd ?? process.cwd());
  const videosDir = path.resolve(cwd, config.videosDir);
  const folder = path.join(videosDir, id);
  if (!folder.startsWith(videosDir + path.sep)) throw new Error('Unsafe video folder');
  const entry = config.entryPointForVideo
    ? path.resolve(cwd, config.entryPointForVideo(id))
    : path.join(folder, 'entry.tsx');
  if (!entry.startsWith(cwd + path.sep)) throw new Error('Entry must be inside the project');
  const title = String(options.title ?? id).trim();
  const duration = Number(options.durationSeconds ?? 5);
  const width = Number(options.width ?? 1080);
  const height = Number(options.height ?? 1920);
  if (!title || !Number.isFinite(duration) || duration <= 0 ||
      !Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0)
    throw new Error('Title, positive duration, and canvas dimensions are required');
  const compositionId = `Video${id.split('-').map((part) => part[0].toUpperCase() + part.slice(1)).join('')}`;
  const authored = [entry, path.join(folder, 'video.tsx'), path.join(folder, 'content', 'video.yaml'),
    path.join(folder, 'layout', 'layoutSpec.ts')];
  for (const file of authored) if (fs.existsSync(file)) throw new Error(`Refusing to replace authored video source: ${file}`);
  for (const file of authored) fs.mkdirSync(path.dirname(file), {recursive: true});
  const scene = path.join(folder, 'video.tsx');
  const configImport = relativeImport(scene, path.join(cwd, 'videogen.config.ts'));
  fs.writeFileSync(scene, `import React from 'react';\nimport project from '${configImport}';\n\n// Replace this starter with the mechanism and visual review for this video.\nexport const Video = () => <div style={{width: '100%', height: '100%', background: project.theme.colors.background, color: project.theme.colors.text, fontFamily: project.theme.fonts.sans, display: 'grid', placeItems: 'center', fontSize: 72, padding: 96, textAlign: 'center'}}>{${JSON.stringify(title)}}</div>;\n`);
  fs.writeFileSync(entry, `import React from 'react';\nimport {Composition, registerRoot} from 'remotion';\nimport {Video} from '${relativeImport(entry, scene).replace(/\\.tsx$/, '')}';\n\n// One entry per draft keeps archived productions out of the edit bundle.\nconst Root = () => <Composition id="${compositionId}" component={Video} width={${width}} height={${height}} fps={30} durationInFrames={${Math.ceil(duration * 30)}}/>;\nregisterRoot(Root);\n`);
  fs.writeFileSync(path.join(folder, 'content', 'video.yaml'), stringify({
    video: {id, title, compositionId, durationSeconds: duration, width, height},
    publishing: {youtube: {title, description: ''}, instagram: {caption: ''}},
  }));
  fs.writeFileSync(path.join(folder, 'layout', 'layoutSpec.ts'), `// The starter title occupies a readable central region. Replace with semantic layout.\nexport function layoutFor(_t: number, width: number, height: number) {\n  return {name: 'starter', boxes: [{label: 'story-title', x: width / 2 - 300, y: height / 2 - 90, w: 600, h: 180, kind: 'region', space: 'screen'}], links: []};\n}\n`);
  const titleFile = path.join(folder, 'title.txt');
  if (!fs.existsSync(titleFile)) fs.writeFileSync(titleFile, `${title}\n`);
  const descriptionFile = path.join(folder, 'description.txt');
  if (!fs.existsSync(descriptionFile)) fs.writeFileSync(descriptionFile, '');
  const manifest = path.join(folder, 'draft.json');
  if (!fs.existsSync(manifest)) fs.writeFileSync(manifest, JSON.stringify({sourceId: id, status: 'draft'}, null, 2) + '\n');
  return {folder, entry, compositionId};
}
