import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {loadContentPackage} from '../scripts/content-package.mjs';

test('custom style is accepted and unregistered style is rejected', () => {
  const root = fs.mkdtempSync(path.join(process.cwd(), 'videogen-test-'));
  const original = process.env.VIDEOGEN_PROJECT;
  try {
    const id = 'custom-story';
    const dir = path.join(root, id);
    fs.mkdirSync(dir);
    fs.writeFileSync(path.join(dir, 'manifest.json'), '{"assets":[]}');
    const content = (style) => `id: ${id}\nstyle: ${style}\ntitle: A custom story\nsource:\n  assetManifest: manifest.json\neditions:\n  post:\n    kind: text\n    heading: A result\n    body: A visible claim\n    caption: A caption\n`;
    fs.writeFileSync(path.join(dir, 'content.yaml'), content('custom-style'));
    const sourceCacheDir = path.join(root, 'analysis', 'source-assets');
    process.env.VIDEOGEN_PROJECT = JSON.stringify({contentDir: root, videosDir: path.join(root, 'videos'), sourceCacheDir, styles: [{id: 'custom-style', name: 'Custom Style', formats: ['post']} ]});
    assert.equal(loadContentPackage(id).style.id, 'custom-style');
    assert.equal(loadContentPackage(id).cacheDir, path.join(sourceCacheDir, id));
    fs.writeFileSync(path.join(dir, 'content.yaml'), content('not-registered'));
    assert.throws(() => loadContentPackage(id), /unknown content style/);
  } finally {
    if (original === undefined) delete process.env.VIDEOGEN_PROJECT;
    else process.env.VIDEOGEN_PROJECT = original;
    fs.rmSync(root, {recursive: true, force: true});
  }
});
