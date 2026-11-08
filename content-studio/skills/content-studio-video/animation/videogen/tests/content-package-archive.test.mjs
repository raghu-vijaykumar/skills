import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {loadContentPackage} from '../scripts/content-package.mjs';

test('a video edition resolves from a published archive folder', () => {
  const root = fs.mkdtempSync(path.join(process.cwd(), 'videogen-archive-test-'));
  const original = process.env.VIDEOGEN_PROJECT;
  try {
    const id = 'archived-story';
    const dir = path.join(root, 'content', id);
    fs.mkdirSync(dir, {recursive: true});
    fs.writeFileSync(path.join(dir, 'manifest.json'), '{"assets":[]}');
    fs.writeFileSync(path.join(dir, 'content.yaml'), `id: ${id}\nstyle: archive-style\ntitle: An archived story\nsource:\n  assetManifest: manifest.json\neditions:\n  video:\n    videoId: 00099-archived-story\n  post:\n    kind: text\n    heading: A result\n    body: A visible claim\n    caption: A caption\n`);
    const videoId = '00099-archived-story';
    const folder = path.join(root, 'long', '2026-01-01 - An Archived Story [abc123]');
    fs.mkdirSync(path.join(folder, 'content'), {recursive: true});
    fs.writeFileSync(path.join(folder, 'source-provenance.json'), JSON.stringify({sourceId: videoId, sourceMatch: 'migrated-current-source'}));
    fs.writeFileSync(path.join(folder, 'content', 'video.yaml'), 'video:\n  style: archive-style\n');
    process.env.VIDEOGEN_PROJECT = JSON.stringify({
      contentDir: path.join(root, 'content'),
      videosDir: path.join(root, 'drafts'),
      publishedDirs: [path.join(root, 'shorts'), path.join(root, 'long')],
      styles: [{id: 'archive-style', name: 'Archive Style', formats: ['video', 'post']}],
    });
    assert.equal(loadContentPackage(id).style.id, 'archive-style');
    fs.writeFileSync(path.join(folder, 'content', 'video.yaml'), 'video:\n  style: other-style\n');
    assert.throws(() => loadContentPackage(id), /must use style archive-style/);
  } finally {
    if (original === undefined) delete process.env.VIDEOGEN_PROJECT;
    else process.env.VIDEOGEN_PROJECT = original;
    fs.rmSync(root, {recursive: true, force: true});
  }
});
