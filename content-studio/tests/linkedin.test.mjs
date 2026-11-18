import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {createDraft, approve, status, approvedStage, renderImage, buildCarousel, runLinkedinCommand} from '../scripts/linkedin-workflow.mjs';
import {authorizationUrl, exchangeCode, loadToken, publishLinkedin, publicationPlan} from '../scripts/linkedin-publish.mjs';

function fixture() {
  const root = path.resolve('tmp');
  fs.mkdirSync(root, {recursive: true});
  const workspace = fs.mkdtempSync(path.join(root, 'content-studio-linkedin-'));
  const id = 'test-opinion';
  const draft = path.join(workspace, 'drafts', id);
  createDraft(workspace, id, 'I think boring systems are often easier to trust.');
  return {workspace, draft, id, cleanup: () => fs.rmSync(workspace, {recursive: true, force: true, maxRetries: 10, retryDelay: 200})};
}
const write = (file, value) => fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
function fillBrief(draft, format, narration = null) {
  write(path.join(draft, 'brief.json'), {angle: 'Boring systems earn trust', stance: 'Simple operations matter',
    audience: 'software professionals', format, formatReason: 'A concrete system example will clarify the opinion',
    brand: 'personal', narration, language: 'English'});
  const planFile = path.join(draft, '.content-studio', 'preflight', 'plan.json');
  const plan = JSON.parse(fs.readFileSync(planFile, 'utf8'));
  const production = plan.steps.find((step) => step.id === 'S04');
  production.method_id = format === 'text' ? 'text-copy' : format === 'image' ? 'content-card' : 'videogen';
  production.inputs = ['post.md', 'creative.json'];
  production.fallback = 'Return to the approved draft for revision';
  if (format !== 'text') production.command = format === 'image'
    ? ['content-studio', 'linkedin', 'render-image', '--draft', 'test-opinion']
    : ['videogen', 'render', 'test-opinion'];
  write(planFile, plan);
}
function makePng(file) {
  const result = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=1080x1350',
    '-frames:v', '1', '-y', file], {encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
}
function makeVideo(file, withAudio) {
  const args = ['-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=1080x1350:r=1',
    ...(withAudio ? ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=8000'] : []),
    '-t', '45', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '32', ...(withAudio ? ['-c:a', 'aac', '-shortest'] : ['-an']), '-y', file];
  const result = spawnSync('ffmpeg', args, {encoding: 'utf8', timeout: 90000});
  assert.equal(result.status, 0, result.stderr?.split(/\r?\n/).slice(-5).join('\n'));
}

test('text draft survives a fresh CLI process and stale edits invalidate review', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'text');
    assert.equal(approve(f.workspace, f.id, 'angle', 'User approved plan and angle').approved, 'angle');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'I prefer systems that are easy to explain.\n');
    approve(f.workspace, f.id, 'draft', 'User approved copy');
    approve(f.workspace, f.id, 'final', 'User reviewed exact text');
    const command = spawnSync(process.execPath, ['content-studio/scripts/cli.mjs', 'linkedin', 'resume', '--workspace', f.workspace,
      '--draft', f.id], {encoding: 'utf8'});
    assert.equal(command.status, 0, command.stderr);
    assert.equal(JSON.parse(command.stdout).nextReview, 'publish');
    assert.equal((await runLinkedinCommand(['publish', '--workspace', f.workspace, '--draft', f.id])).dryRun, true);
    fs.appendFileSync(path.join(f.draft, 'post.md'), ' Changed.');
    assert.equal(status(f.workspace, f.id).approved, 'angle');
    await assert.rejects(runLinkedinCommand(['publish', '--workspace', f.workspace, '--draft', f.id]), /approval.*stale/);
    const plan = path.join(f.draft, '.content-studio', 'preflight', 'plan.json');
    fs.appendFileSync(plan, ' ');
    assert.equal(approvedStage(f.draft), null);
  } finally { f.cleanup(); }
});

test('facts require URLs and image approval validates original art provenance', () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'image');
    write(path.join(f.draft, 'sources.json'), {claims: [{text: 'A fact', type: 'fact'}], assets: []});
    assert.throws(() => approve(f.workspace, f.id, 'angle', 'Review'), /source URL/);
    write(path.join(f.draft, 'sources.json'), {claims: [{text: 'A fact', type: 'fact', sourceUrl: 'https://example.com'}], assets: []});
    approve(f.workspace, f.id, 'angle', 'User approved angle');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'A considered take.\n');
    write(path.join(f.draft, 'creative.json'), {imageConcept: 'Simple schematic', altText: 'A simple schematic',
      mediaOrigin: 'original-illustration', assetMethod: 'Code drawn', card: {heading: 'A simple point', body: 'Show the mechanism'}});
    approve(f.workspace, f.id, 'draft', 'User approved visual plan');
    makePng(path.join(f.draft, 'image.png'));
    approve(f.workspace, f.id, 'final', 'User reviewed exact image');
    assert.equal(publicationPlan(f.draft).format, 'image');
  } finally { f.cleanup(); }
});

test('content card renders an original illustration without evidence labelling', {skip: !process.env.CONTENT_STUDIO_RENDER_TESTS}, async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'image');
    approve(f.workspace, f.id, 'angle', 'User approved visual route');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'An illustrated opinion.\n');
    makePng(path.join(f.draft, 'illustration.png'));
    write(path.join(f.draft, 'creative.json'), {imageConcept: 'Simple schematic', altText: 'Simple schematic',
      mediaOrigin: 'original-illustration', assetMethod: 'Code drawn', illustrationPath: 'illustration.png',
      card: {heading: 'The simple route', body: 'Explain the point'}});
    approve(f.workspace, f.id, 'draft', 'User approved card');
    const result = await renderImage(f.workspace, f.id);
    assert.equal(result.width, 1080);
    if (process.env.CONTENT_STUDIO_KEEP_RENDER) fs.copyFileSync(result.file, path.resolve('tmp', 'linkedin-render-evidence.png'));
    approve(f.workspace, f.id, 'final', 'User reviewed image');
  } finally { f.cleanup(); }
});

test('narrated and silent video packages enforce their own final assets', {skip: !process.env.CONTENT_STUDIO_MEDIA_TESTS}, () => {
  for (const narration of ['narrated', 'silent']) {
    const f = fixture();
    try {
      fillBrief(f.draft, 'video', narration);
      approve(f.workspace, f.id, 'angle', 'User approved video route');
      fs.writeFileSync(path.join(f.draft, 'post.md'), 'A systems lesson.\n');
      write(path.join(f.draft, 'creative.json'), {script: 'Explain one failure mode.', storyboard: [{id: 'beat-1', visual: 'Show two nodes'}],
        coverConcept: 'Two nodes'});
      approve(f.workspace, f.id, 'draft', 'User approved script');
      makeVideo(path.join(f.draft, 'video.mp4'), narration === 'narrated');
      makePng(path.join(f.draft, 'cover.png'));
      if (narration === 'narrated') fs.writeFileSync(path.join(f.draft, 'captions.srt'), '1\n00:00:00,000 --> 00:00:02,000\nOne failure mode.\n');
      approve(f.workspace, f.id, 'final', 'User reviewed full video');
      assert.equal(status(f.workspace, f.id).approved, 'final');
    } finally { f.cleanup(); }
  }
});

test('animated image accepts an independently produced GIF with reviewed motion', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'animated-image');
    const brief = JSON.parse(fs.readFileSync(path.join(f.draft, 'brief.json')));
    brief.brand = 'project-blue';
    write(path.join(f.draft, 'brief.json'), brief);
    fs.mkdirSync(path.join(f.workspace, 'presets'));
    write(path.join(f.workspace, 'presets', 'project-blue.json'), {name: 'Project Blue',
      theme: {id: 'project-blue', brand: 'PROJECT BLUE', colors: {accent: '#3355ff'},
        fonts: {sans: 'Arial', mono: 'Consolas'}}});
    approve(f.workspace, f.id, 'angle', 'User approved custom project preset and GIF method');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'A moving explanation.\n');
    write(path.join(f.draft, 'creative.json'), {imageConcept: 'Two states', altText: 'A diagram alternates states',
      mediaOrigin: 'original-illustration', assetMethod: 'Programmatic drawing', motionPlan: 'Reveal one transition'});
    approve(f.workspace, f.id, 'draft', 'User approved motion and copy');
    const result = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
      '-i', 'testsrc=s=1080x1350:r=2', '-frames:v', '2', '-y', path.join(f.draft, 'animation.gif')], {encoding: 'utf8'});
    assert.equal(result.status, 0, result.stderr);
    approve(f.workspace, f.id, 'final', 'User reviewed exact animation');
    assert.equal(publicationPlan(f.draft).format, 'animated-image');
    const dry = await runLinkedinCommand(['publish', '--workspace', f.workspace, '--draft', f.id]);
    assert.match(dry.files.media, /^[a-f0-9]{64}$/);
    const token = {accessToken: 'token', memberUrn: 'urn:li:person:123'};
    const fake = async (url, request) => {
      if (url.includes('images?action=initializeUpload')) return new Response(JSON.stringify({value: {
        uploadUrl: 'https://upload.local/gif', image: 'urn:li:image:gif'}}));
      if (url === 'https://upload.local/gif') return new Response('', {status: 201});
      assert.equal(JSON.parse(request.body).content.media.altText, 'A diagram alternates states');
      return new Response('', {status: 201, headers: {'x-restli-id': 'urn:li:share:888'}});
    };
    await publishLinkedin(f.draft, f.workspace, {}, fake);
    assert.equal((await publishLinkedin(f.draft, f.workspace, {confirm: true,
      authorizationNote: 'User approved this post', token}, fake)).postId, 'urn:li:share:888');
    write(path.join(f.workspace, 'presets', 'project-blue.json'), {name: 'Project Blue Revised'});
    assert.equal(approvedStage(f.draft), null);
  } finally { f.cleanup(); }
});

test('information carousel assembles portrait slides as a document post', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'carousel');
    approve(f.workspace, f.id, 'angle', 'User approved the PDF document route');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'A two-page explanation.\n');
    write(path.join(f.draft, 'creative.json'), {title: 'Two useful steps', slideOutline: ['The problem', 'The fix']});
    approve(f.workspace, f.id, 'draft', 'User approved copy and slide sequence');
    fs.mkdirSync(path.join(f.draft, 'slides'));
    makePng(path.join(f.draft, 'slides', '01.png'));
    makePng(path.join(f.draft, 'slides', '02.png'));
    const built = buildCarousel(f.workspace, f.id);
    assert.equal(built.pages, 2);
    approve(f.workspace, f.id, 'final', 'User reviewed each slide and full PDF');
    const dry = await runLinkedinCommand(['publish', '--workspace', f.workspace, '--draft', f.id]);
    assert.equal(dry.format, 'carousel');
    assert.match(dry.files.media, /^[a-f0-9]{64}$/);
    const token = {accessToken: 'token', memberUrn: 'urn:li:person:123'};
    const calls = [];
    const fake = async (url, request) => {
      calls.push(url);
      if (url.includes('documents?action=initializeUpload')) return new Response(JSON.stringify({value: {
        uploadUrl: 'https://upload.local/document', document: 'urn:li:document:abc'}}));
      if (url === 'https://upload.local/document') { assert.equal(request.method, 'PUT'); return new Response('', {status: 201}); }
      if (url.includes('/documents/')) return new Response(JSON.stringify({status: 'AVAILABLE'}));
      if (url.endsWith('/posts')) {
        assert.deepEqual(JSON.parse(request.body).content.media, {id: 'urn:li:document:abc', title: 'Two useful steps'});
        return new Response('', {status: 201, headers: {'x-restli-id': 'urn:li:share:777'}});
      }
      throw new Error(`Unexpected URL ${url}`);
    };
    await publishLinkedin(f.draft, f.workspace, {}, fake);
    const result = await publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'User approved this post', token}, fake);
    assert.equal(result.postId, 'urn:li:share:777');
    assert.equal(calls.filter((url) => url.endsWith('/posts')).length, 1);
  } finally { f.cleanup(); }
});

test('OAuth exchange checks scope and stores member identity without exposing token in results', async () => {
  const url = authorizationUrl('client', 'http://127.0.0.1:53621/callback', 'state');
  assert.match(url, /w_member_social/);
  const fake = async (endpoint) => endpoint.endsWith('accessToken')
    ? new Response(JSON.stringify({access_token: 'private', expires_in: 3600, scope: 'openid profile w_member_social'}))
    : new Response(JSON.stringify({sub: '123', name: 'A Person'}));
  const token = await exchangeCode({clientId: 'client', clientSecret: 'private'}, 'code', 'http://127.0.0.1:53621/callback', fake);
  assert.equal(token.memberUrn, 'urn:li:person:123');
  const noScope = async (endpoint) => endpoint.endsWith('accessToken')
    ? new Response(JSON.stringify({access_token: 'private', expires_in: 3600}))
    : new Response(JSON.stringify({sub: '123'}));
  await assert.rejects(exchangeCode({clientId: 'client', clientSecret: 'private'}, 'code',
    'http://127.0.0.1:53621/callback', noScope), /did not confirm w_member_social/);
  const f = fixture();
  try {
    fs.mkdirSync(path.join(f.workspace, 'secrets'));
    write(path.join(f.workspace, 'secrets', 'linkedin-token.json'), {...token, expiresAt: '2000-01-01T00:00:00Z'});
    assert.throws(() => loadToken(f.workspace), /expired/);
  } finally { f.cleanup(); }
});

test('text publisher creates one post and blocks uncertain retries', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'text');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'An approved opinion.\n');
    const token = {accessToken: 'token', memberUrn: 'urn:li:person:123'};
    let calls = 0;
    const fake = async (url, request) => {
      assert.equal(url, 'https://api.linkedin.com/rest/posts');
      assert.equal(JSON.parse(request.body).commentary, 'An approved opinion.');
      calls++;
      return new Response('', {status: 201, headers: {'x-restli-id': 'urn:li:share:12345'}});
    };
    await assert.rejects(publishLinkedin(f.draft, f.workspace,
      {confirm: true, authorizationNote: 'User asked to post', token}, fake), /dry run/);
    assert.equal((await publishLinkedin(f.draft, f.workspace, {}, fake)).dryRun, true);
    const result = await publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'User asked to post', token}, fake);
    assert.equal(result.postId, 'urn:li:share:12345');
    assert.equal(calls, 1);
    await assert.rejects(publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'Again', token}, fake), /already recorded/);
    fs.rmSync(path.join(f.draft, 'linkedin-receipt.json'));
    const ambiguous = async () => { throw new Error('connection closed'); };
    await assert.rejects(publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'User asked to post', token}, ambiguous), /connection closed/);
    await assert.rejects(publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'Retry', token}, fake), /may have succeeded/);
  } finally { f.cleanup(); }
});

test('image publisher uploads before posting and an access denial leaves package intact', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'image');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'An image opinion.\n');
    write(path.join(f.draft, 'creative.json'), {altText: 'Diagram', title: 'An idea'});
    makePng(path.join(f.draft, 'image.png'));
    const token = {accessToken: 'token', memberUrn: 'urn:li:person:123'};
    let posts = 0;
    const fake = async (url, request) => {
      if (url.includes('images?action=initializeUpload')) return new Response(JSON.stringify({value: {uploadUrl: 'https://upload.local/image', image: 'urn:li:image:abc'}}));
      if (url === 'https://upload.local/image') return new Response('', {status: 201});
      posts++;
      assert.equal(JSON.parse(request.body).content.media.altText, 'Diagram');
      return new Response(JSON.stringify({message: 'access denied'}), {status: 403});
    };
    await publishLinkedin(f.draft, f.workspace, {}, fake);
    await assert.rejects(publishLinkedin(f.draft, f.workspace, {confirm: true, authorizationNote: 'User asked to post', token}, fake), /403/);
    assert.equal(posts, 1);
    assert.equal(fs.existsSync(path.join(f.draft, 'image.png')), true);
    assert.equal(JSON.parse(fs.readFileSync(path.join(f.draft, 'linkedin-receipt.json'))).postAttemptedAt, undefined);
  } finally { f.cleanup(); }
});

test('video publisher uploads parts, cover and captions before creating one post', async () => {
  const f = fixture();
  try {
    fillBrief(f.draft, 'video', 'narrated');
    fs.writeFileSync(path.join(f.draft, 'post.md'), 'A narrated lesson.\n');
    write(path.join(f.draft, 'creative.json'), {title: 'A lesson'});
    fs.writeFileSync(path.join(f.draft, 'video.mp4'), 'abc');
    fs.writeFileSync(path.join(f.draft, 'cover.png'), 'cover');
    fs.writeFileSync(path.join(f.draft, 'captions.srt'), '1\n00:00:00,000 --> 00:00:01,000\nHello\n');
    const token = {accessToken: 'token', memberUrn: 'urn:li:person:123'};
    const calls = [];
    let reads = 0;
    const fake = async (url, request) => {
      calls.push(url);
      if (url.includes('videos?action=initializeUpload')) return new Response(JSON.stringify({value: {
        video: 'urn:li:video:abc', uploadInstructions: [{firstByte: 0, lastByte: 2, uploadUrl: 'https://upload.local/part'}],
        uploadToken: '', thumbnailUploadUrl: 'https://upload.local/cover', captionsUploadUrl: 'https://upload.local/captions'}}));
      if (url.endsWith('/part')) return new Response('', {status: 200, headers: {etag: 'part-id'}});
      if (url.endsWith('/cover') || url.endsWith('/captions')) return new Response('', {status: 201});
      if (url.includes('videos?action=finalizeUpload')) {
        assert.deepEqual(JSON.parse(request.body).finalizeUploadRequest.uploadedPartIds, ['part-id']);
        return new Response('{}');
      }
      if (url.includes('videos/urn%3Ali%3Avideo%3Aabc')) return new Response(JSON.stringify({status: ++reads === 1 ? 'PROCESSING' : 'AVAILABLE'}));
      if (url.endsWith('/posts')) {
        assert.equal(JSON.parse(request.body).content.media.id, 'urn:li:video:abc');
        return new Response('', {status: 201, headers: {'x-restli-id': 'urn:li:ugcPost:999'}});
      }
      throw new Error(`Unexpected URL ${url}`);
    };
    await publishLinkedin(f.draft, f.workspace, {}, fake);
    const result = await publishLinkedin(f.draft, f.workspace,
      {confirm: true, authorizationNote: 'User asked to post', token, sleep: async () => {}}, fake);
    assert.equal(result.postId, 'urn:li:ugcPost:999');
    assert.equal(calls.filter((url) => url.endsWith('/posts')).length, 1);
    assert.ok(calls.findIndex((url) => url.endsWith('/captions')) < calls.findIndex((url) => url.endsWith('/posts')));
  } finally { f.cleanup(); }
});
