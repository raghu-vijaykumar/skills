import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {parse} from 'yaml';
import {scaffoldDraft} from '../scripts/scaffold.mjs';

const scratch = path.resolve('tmp');
fs.mkdirSync(scratch, {recursive: true});
test('scaffold creates one independent composition and preserves an idea brief', () => {
  const cwd = fs.mkdtempSync(path.join(scratch, 'videogen-scaffold-'));
  try {
    fs.writeFileSync(path.join(cwd, 'videogen.config.ts'), 'export default {};\n');
    const draft = path.join(cwd, 'drafts', '00077-new-idea');
    fs.mkdirSync(draft, {recursive: true});
    fs.writeFileSync(path.join(draft, 'brief.md'), 'Original idea\n');
    fs.writeFileSync(path.join(draft, 'draft.json'), '{"sourceId":"00077-new-idea","status":"draft"}\n');
    const config = {videosDir: 'drafts', entryPointForVideo: (id) => `drafts/${id}/entry.tsx`};
    const result = scaffoldDraft(config, '00077-new-idea', {cwd, title: 'Why things happen'});
    assert.equal(result.compositionId, 'Video00077NewIdea');
    assert.match(fs.readFileSync(result.entry, 'utf8'), /registerRoot\(Root\)/);
    assert.match(fs.readFileSync(path.join(draft, 'video.tsx'), 'utf8'), /Why things happen/);
    assert.equal(parse(fs.readFileSync(path.join(draft, 'content', 'video.yaml'), 'utf8')).video.compositionId,
      'Video00077NewIdea');
    assert.equal(fs.readFileSync(path.join(draft, 'brief.md'), 'utf8'), 'Original idea\n');
    assert.throws(() => scaffoldDraft(config, '00077-new-idea', {cwd}), /Refusing to replace/);
    assert.throws(() => scaffoldDraft(config, '../escape', {cwd}), /Invalid video ID/);
  } finally {
    if (!cwd.startsWith(scratch + path.sep)) throw new Error('Unsafe fixture cleanup');
    fs.rmSync(cwd, {recursive: true, force: true});
  }
});
