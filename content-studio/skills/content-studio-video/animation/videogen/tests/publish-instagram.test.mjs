import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {test} from 'node:test';
import {instagramPlan, publishInstagram} from '../scripts/publish-instagram.mjs';

const tempRoot = path.resolve('tmp');
fs.mkdirSync(tempRoot, {recursive: true});
function fixture() {
  const root = fs.mkdtempSync(path.join(tempRoot, 'videogen-instagram-'));
  const draft = path.join(root, 'drafts', '001-test');
  fs.mkdirSync(draft, {recursive: true});
  fs.mkdirSync(path.join(root, 'secrets'));
  fs.writeFileSync(path.join(root, 'secrets', 'instagram-token.json'), JSON.stringify({accessToken: 'access', igUserId: '123'}));
  fs.writeFileSync(path.join(draft, 'video.mp4'), 'source bytes');
  fs.writeFileSync(path.join(draft, 'content.txt'), 'authored');
  const item = {dir: draft, value: {video: {id: '001-test'}, publishing: {instagram: {caption: 'Reel caption #test'}}}};
  execFileSync('git', ['-C', root, 'init', '-b', 'main'], {stdio: 'ignore'});
  execFileSync('git', ['-C', root, 'add', '.'], {stdio: 'ignore'});
  execFileSync('git', ['-C', root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'fixture'], {stdio: 'ignore'});
  return {root, draft, item};
}
function cleanup(root) {
  if (!path.resolve(root).startsWith(tempRoot + path.sep)) throw new Error(`Unsafe test cleanup: ${root}`);
  fs.rmSync(root, {recursive: true, force: true});
}
const response = (body, status = 200) => new Response(JSON.stringify(body), {status});

test('Instagram dry run validates caption without credentials or network', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  try {
    process.chdir(root);
    fs.rmSync(path.join(root, 'secrets', 'instagram-token.json'));
    const result = await publishInstagram(item, {}, {}, () => { throw new Error('network called'); });
    assert.equal(result.dryRun, true);
    assert.equal(result.caption, 'Reel caption #test');
    assert.equal(fs.existsSync(path.join(draft, 'draft.json')), false);
    item.value.publishing.instagram.caption = '';
    assert.throws(() => instagramPlan(item), /caption is required/);
    item.value.publishing.instagram.caption = `${'#a '.repeat(31)}`;
    assert.throws(() => instagramPlan(item), /30 hashtags/);
  } finally { process.chdir(previous); cleanup(root); }
});

test('Instagram persists container, tolerates an upload error after FINISHED, and blocks duplicate publishing', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  let uploaded = 0;
  let published = 0;
  let statuses = 0;
  const fakeFetch = async (url, options) => {
    if (url.endsWith('/123/media')) return response({id: 'container1', uri: 'https://rupload.facebook.com/ig-api-upload/v25.0/container1'});
    if (url.includes('container1?')) return response({status_code: ++statuses === 1 ? 'IN_PROGRESS' : 'FINISHED'});
    if (url.includes('rupload.facebook.com')) {
      uploaded++;
      for await (const _ of options.body) { /* Consume the upload stream. */ }
      return response({message: 'unreliable response'}, 400);
    }
    if (url.endsWith('/123/media_publish')) { published++; return response({id: 'ig123'}); }
    throw new Error(`Unexpected URL ${url}`);
  };
  try {
    process.chdir(root);
    const result = await publishInstagram(item, {}, {confirm: true, prepare: (plan) => plan.render}, fakeFetch);
    assert.equal(result.instagramId, 'ig123');
    assert.equal(uploaded, 1);
    assert.equal(published, 1);
    const receipt = JSON.parse(fs.readFileSync(path.join(draft, 'draft.json')));
    assert.equal(receipt.instagramContainerId, 'container1');
    assert.equal(receipt.instagramId, 'ig123');
    await assert.rejects(publishInstagram(item, {}, {confirm: true, prepare: (plan) => plan.render}, fakeFetch), /already recorded/);
    assert.equal(published, 1);
  } finally { process.chdir(previous); cleanup(root); }
});

test('Instagram refuses a second publish after an uncertain API response', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  let published = 0;
  const fakeFetch = async (url) => {
    if (url.endsWith('/123/media')) return response({id: 'container2', uri: 'https://rupload.facebook.com/ig-api-upload/v25.0/container2'});
    if (url.includes('container2?')) return response({status_code: 'FINISHED'});
    if (url.endsWith('/123/media_publish')) { published++; return response({error: {message: 'unavailable'}}, 500); }
    throw new Error(`Unexpected URL ${url}`);
  };
  try {
    process.chdir(root);
    await assert.rejects(publishInstagram(item, {}, {confirm: true, prepare: (plan) => plan.render}, fakeFetch), /unavailable/);
    const receipt = JSON.parse(fs.readFileSync(path.join(draft, 'draft.json')));
    assert.ok(receipt.instagramPublishAttemptedAt);
    await assert.rejects(publishInstagram(item, {}, {confirm: true, resume: true, prepare: (plan) => plan.render}, fakeFetch), /may have succeeded/);
    assert.equal(published, 1);
  } finally { process.chdir(previous); cleanup(root); }
});

test('Instagram rejects scheduling and changed render on resume', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  try {
    process.chdir(root);
    await assert.rejects(publishInstagram(item, {}, {at: '2030-01-01T00:00:00Z'}), /does not support native scheduling/);
    fs.writeFileSync(path.join(draft, 'draft.json'), JSON.stringify({instagramContainerId: 'existing', instagramRenderSha256: 'old', instagramCaption: 'Reel caption #test'}));
    await assert.rejects(publishInstagram(item, {}, {confirm: true, resume: true}), /differs from current/);
  } finally { process.chdir(previous); cleanup(root); }
});

test('Instagram resumes a finished container without creating or uploading a second one', async () => {
  const {root, draft, item} = fixture();
  const previous = process.cwd();
  let publishes = 0;
  try {
    process.chdir(root);
    const {createHash} = await import('node:crypto');
    const sha = createHash('sha256').update(fs.readFileSync(path.join(draft, 'video.mp4'))).digest('hex');
    fs.writeFileSync(path.join(draft, 'draft.json'), JSON.stringify({instagramContainerId: 'container3',
      instagramRenderSha256: sha, instagramCaption: 'Reel caption #test', instagramSourceCommit: 'fixture',
      instagramUploadUri: 'https://rupload.facebook.com/ig-api-upload/v25.0/container3', instagramStatus: 'container-created'}));
    const fakeFetch = async (url) => {
      if (url.includes('container3?')) return response({status_code: 'FINISHED'});
      if (url.endsWith('/123/media_publish')) { publishes++; return response({id: 'ig-resumed'}); }
      throw new Error(`Unexpected URL ${url}`);
    };
    const result = await publishInstagram(item, {}, {confirm: true, resume: true, prepare: (plan) => plan.render}, fakeFetch);
    assert.equal(result.instagramId, 'ig-resumed');
    assert.equal(publishes, 1);
  } finally { process.chdir(previous); cleanup(root); }
});
