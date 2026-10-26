import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {test} from 'node:test';
import {publicationPlan, publishYoutube, selectMaster} from '../scripts/publish-youtube.mjs';

const tempRoot = path.resolve('tmp');
fs.mkdirSync(tempRoot, {recursive: true});
function cleanup(root) {
  if (!path.resolve(root).startsWith(tempRoot + path.sep)) throw new Error(`Unsafe test cleanup: ${root}`);
  fs.rmSync(root, {recursive: true, force: true});
}
function fixture() {
  const root = fs.mkdtempSync(path.join(tempRoot, 'videogen-publish-'));
  const draft = path.join(root, 'drafts', '001-test');
  fs.mkdirSync(draft, {recursive: true});
  fs.writeFileSync(path.join(draft, 'video.mp4'), 'render-bytes');
  fs.writeFileSync(path.join(draft, 'thumbnail.jpg'), 'thumbnail');
  fs.writeFileSync(path.join(draft, 'title.txt'), 'Exact title\n');
  fs.writeFileSync(path.join(draft, 'description.txt'), 'Exact description\n');
  const item = {dir: draft, value: {video: {id: '001-test', title: 'Exact title'},
    publishing: {youtube: {title: 'Exact title', description: 'Exact description'}}}};
  return {root, draft, item};
}

test('selectMaster excludes range renders and requires exact metadata', () => {
  const {root, draft, item} = fixture();
  try {
    assert.equal(selectMaster(draft, '001-test'), path.join(draft, 'video.mp4'));
    assert.equal(publicationPlan(item, {}).title, 'Exact title');
    fs.unlinkSync(path.join(draft, 'video.mp4'));
    fs.mkdirSync(path.join(draft, 'assets', 'generated', 'video'), {recursive: true});
    fs.writeFileSync(path.join(draft, 'assets', 'generated', 'video', '001-test-1440x2560-30-2-5.mp4'), 'range');
    assert.throws(() => selectMaster(draft, '001-test'), /no full-length MP4/);
    fs.writeFileSync(path.join(draft, 'video.mp4'), 'render-bytes');
    fs.writeFileSync(path.join(draft, 'description.txt'), 'stale description\n');
    assert.throws(() => publicationPlan(item, {}), /must match/);
  } finally { cleanup(root); }
});

test('partial thumbnail failure records YouTube ID and resume never uploads again', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  let uploads = 0;
  let thumbnails = 0;
  try {
    fs.mkdirSync(path.join(root, 'secrets'));
    fs.writeFileSync(path.join(root, 'secrets', 'youtube-client.json'), JSON.stringify({installed: {client_id: 'client', client_secret: 'secret'}}));
    fs.writeFileSync(path.join(root, 'secrets', 'youtube-token.json'), JSON.stringify({refreshToken: 'refresh'}));
    execFileSync('git', ['-C', root, 'init', '-b', 'main'], {stdio: 'ignore'});
    execFileSync('git', ['-C', root, 'add', '.'], {stdio: 'ignore'});
    execFileSync('git', ['-C', root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'fixture'], {stdio: 'ignore'});
    process.chdir(root);
    const response = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {status, headers});
    const fakeFetch = async (url, options) => {
      if (url.includes('/token')) return response({access_token: 'access'});
      if (url.includes('uploadType=resumable')) return response({}, 200, {location: 'https://upload.example/session'});
      if (url === 'https://upload.example/session') {
        uploads++;
        for await (const _ of options.body) { /* Consume the test upload stream. */ }
        return response({id: 'abcdefghijk'});
      }
      if (url.includes('/thumbnails/set')) {
        thumbnails++;
        return thumbnails === 1 ? response({error: {message: 'retry'}}, 500) : response({items: []});
      }
      throw new Error(`Unexpected URL ${url}`);
    };
    await assert.rejects(publishYoutube(item, {}, {confirm: true}, fakeFetch), /retry/);
    const recorded = JSON.parse(fs.readFileSync(path.join(draft, 'draft.json')));
    assert.equal(recorded.youtubeId, 'abcdefghijk');
    assert.equal(recorded.thumbnailSet, false);
    await assert.rejects(publishYoutube(item, {}, {confirm: true}, fakeFetch), /already recorded/);
    const resumed = await publishYoutube(item, {}, {confirm: true, resume: true}, fakeFetch);
    assert.equal(resumed.youtubeId, 'abcdefghijk');
    assert.equal(uploads, 1);
    assert.equal(JSON.parse(fs.readFileSync(path.join(draft, 'draft.json'))).thumbnailSet, true);
  } finally {
    process.chdir(previous);
    cleanup(root);
  }
});
