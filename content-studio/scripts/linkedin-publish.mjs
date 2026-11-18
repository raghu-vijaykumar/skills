// LinkedIn media uploads are resumable, but the final post create call is never retried blindly.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {randomBytes, createHash} from 'node:crypto';

const API = 'https://api.linkedin.com/rest';
const AUTH = 'https://www.linkedin.com/oauth/v2';
const TOKEN_FILE = path.join('secrets', 'linkedin-token.json');
const sha = (file) => {
  const digest = createHash('sha256');
  const handle = fs.openSync(file, 'r');
  const block = Buffer.alloc(1024 * 1024);
  try { let size; while ((size = fs.readSync(handle, block, 0, block.length, null)) > 0) digest.update(block.subarray(0, size)); }
  finally { fs.closeSync(handle); }
  return digest.digest('hex');
};
const read = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
function save(file, value, privateFile = false) {
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const temp = `${file}.tmp`;
  fs.writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, {mode: privateFile ? 0o600 : 0o644});
  fs.renameSync(temp, file);
}
function responseError(response, body) {
  return new Error(`LinkedIn API ${response.status}: ${body?.message ?? body?.error_description ?? body?.error ?? 'request failed'}`);
}
async function data(response) {
  const raw = await response.text();
  let body;
  try { body = raw ? JSON.parse(raw) : {}; } catch { body = {message: raw.slice(0, 500)}; }
  if (!response.ok) throw responseError(response, body);
  return body;
}
function headers(token, version = '202610') {
  if (!/^20\d{4}$/.test(version)) throw new Error('LinkedIn API version must be YYYYMM');
  return {Authorization: `Bearer ${token}`, 'Linkedin-Version': version, 'X-Restli-Protocol-Version': '2.0.0'};
}
function tokenPath(workspace) { return path.join(workspace, TOKEN_FILE); }

export function authorizationUrl(clientId, redirectUri, state) {
  const query = new URLSearchParams({response_type: 'code', client_id: clientId, redirect_uri: redirectUri,
    state, scope: 'openid profile w_member_social'});
  return `${AUTH}/authorization?${query}`;
}

export async function exchangeCode(client, code, redirectUri, fetchImpl = fetch) {
  const response = await fetchImpl(`${AUTH}/accessToken`, {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({grant_type: 'authorization_code', code, redirect_uri: redirectUri,
      client_id: client.clientId, client_secret: client.clientSecret})});
  const token = await data(response);
  if (!token.access_token || !Number.isFinite(Number(token.expires_in))) throw new Error('LinkedIn token response is incomplete');
  if (!token.scope?.split(/\s+/).includes('w_member_social')) throw new Error('Connected app did not confirm w_member_social');
  const profile = await data(await fetchImpl('https://api.linkedin.com/v2/userinfo', {headers: {Authorization: `Bearer ${token.access_token}`}}));
  if (!profile.sub) throw new Error('LinkedIn userinfo has no member ID');
  return {accessToken: token.access_token, expiresAt: new Date(Date.now() + Number(token.expires_in) * 1000).toISOString(),
    scope: token.scope, memberUrn: `urn:li:person:${profile.sub}`,
    displayName: profile.name ?? null, connectedAt: new Date().toISOString()};
}

export async function connectLinkedin(workspace, {clientFile, port} = {}, fetchImpl = fetch) {
  const file = path.resolve(clientFile ?? path.join(workspace, 'secrets', 'linkedin-client.json'));
  if (!fs.existsSync(file)) throw new Error(`Create an ignored LinkedIn client file with clientId and clientSecret: ${file}`);
  const client = read(file);
  if (!client.clientId || !client.clientSecret) throw new Error('LinkedIn client file needs clientId and clientSecret');
  const number = Number(port ?? 53621);
  if (!Number.isInteger(number) || number < 1024 || number > 65535) throw new Error('Port must be 1024–65535');
  const redirectUri = `http://127.0.0.1:${number}/callback`;
  const state = randomBytes(24).toString('hex');
  const code = await new Promise((resolve, reject) => {
    let timeout;
    const server = http.createServer((request, response) => {
      const url = new URL(request.url, redirectUri);
      if (url.pathname !== '/callback') { response.writeHead(404); response.end(); return; }
      const finish = (error, value) => { clearTimeout(timeout); server.close(); error ? reject(error) : resolve(value); };
      if (url.searchParams.get('state') !== state) { response.writeHead(400); response.end('OAuth state mismatch'); finish(new Error('LinkedIn OAuth state mismatch')); return; }
      if (url.searchParams.get('error')) { response.writeHead(400); response.end('LinkedIn authorization declined'); finish(new Error(`LinkedIn authorization: ${url.searchParams.get('error')}`)); return; }
      const received = url.searchParams.get('code');
      if (!received) { response.writeHead(400); response.end('Missing code'); finish(new Error('LinkedIn OAuth code missing')); return; }
      response.writeHead(200, {'Content-Type': 'text/plain'}); response.end('LinkedIn connected. Return to Content Studio.');
      finish(null, received);
    });
    server.on('error', reject);
    server.listen(number, '127.0.0.1', () => {
      process.stdout.write(`Open this LinkedIn authorization URL:\n${authorizationUrl(client.clientId, redirectUri, state)}\n`);
    });
    timeout = setTimeout(() => { server.close(); reject(new Error('LinkedIn authorization timed out')); }, 5 * 60 * 1000);
  });
  const token = await exchangeCode(client, code, redirectUri, fetchImpl);
  save(tokenPath(workspace), token, true);
  return {connected: true, memberUrn: token.memberUrn, displayName: token.displayName, expiresAt: token.expiresAt};
}

export function loadToken(workspace) {
  const file = tokenPath(workspace);
  if (!fs.existsSync(file)) throw new Error('LinkedIn is not connected; run linkedin connect');
  const token = read(file);
  if (!token.accessToken || !/^urn:li:person:/.test(token.memberUrn ?? '') ||
      !token.scope?.split(/\s+/).includes('w_member_social')) throw new Error('LinkedIn token lacks member publishing permission');
  if (Date.parse(token.expiresAt) <= Date.now() + 5 * 60 * 1000) throw new Error('LinkedIn token expired; reconnect before publishing');
  return token;
}

export function publicationPlan(draft) {
  const brief = read(path.join(draft, 'brief.json'));
  const creative = read(path.join(draft, 'creative.json'));
  const copy = fs.readFileSync(path.join(draft, 'post.md'), 'utf8').trim();
  if (!copy) throw new Error('LinkedIn post copy is empty');
  const format = brief.format;
  const mediaName = {image: 'image.png', 'animated-image': 'animation.gif', carousel: 'carousel.pdf', video: 'video.mp4'}[format];
  const media = mediaName ? path.join(draft, mediaName) : null;
  if (!['text', 'image', 'animated-image', 'carousel', 'video'].includes(format) || (media && !fs.existsSync(media)))
    throw new Error('LinkedIn final media is missing or format is invalid');
  const files = {post: sha(path.join(draft, 'post.md')), brief: sha(path.join(draft, 'brief.json')),
    creative: sha(path.join(draft, 'creative.json')), ...(media ? {media: sha(media)} : {})};
  if (format === 'video') {
    files.cover = sha(path.join(draft, 'cover.png'));
    if (brief.narration === 'narrated') files.captions = sha(path.join(draft, 'captions.srt'));
  }
  const fingerprint = createHash('sha256').update(JSON.stringify(files)).digest('hex');
  return {format, copy, media, cover: format === 'video' ? path.join(draft, 'cover.png') : null,
    captions: format === 'video' && brief.narration === 'narrated' ? path.join(draft, 'captions.srt') : null,
    title: String(creative.title ?? brief.angle).trim(), altText: creative.altText ?? null, files, fingerprint};
}

async function uploadImage(plan, token, version, fetchImpl) {
  const apiHeaders = {...headers(token.accessToken, version), 'Content-Type': 'application/json'};
  const initialized = await data(await fetchImpl(`${API}/images?action=initializeUpload`, {method: 'POST', headers: apiHeaders,
    body: JSON.stringify({initializeUploadRequest: {owner: token.memberUrn}})}));
  const {uploadUrl, image} = initialized.value ?? {};
  if (!uploadUrl || !image) throw new Error('LinkedIn image upload initialization is incomplete');
  const response = await fetchImpl(uploadUrl, {method: 'PUT', headers: {'Content-Type': 'application/octet-stream'}, body: fs.readFileSync(plan.media)});
  if (!response.ok) throw responseError(response, await response.json().catch(() => ({})));
  return image;
}

async function uploadDocument(plan, token, version, fetchImpl, sleep) {
  const apiHeaders = {...headers(token.accessToken, version), 'Content-Type': 'application/json'};
  const initialized = await data(await fetchImpl(`${API}/documents?action=initializeUpload`, {method: 'POST', headers: apiHeaders,
    body: JSON.stringify({initializeUploadRequest: {owner: token.memberUrn}})}));
  const {uploadUrl, document} = initialized.value ?? {};
  if (!uploadUrl || !document) throw new Error('LinkedIn document upload initialization is incomplete');
  const uploaded = await fetchImpl(uploadUrl, {method: 'PUT',
    headers: {Authorization: `Bearer ${token.accessToken}`, 'Content-Type': 'application/pdf'}, body: fs.readFileSync(plan.media)});
  if (!uploaded.ok) throw responseError(uploaded, await uploaded.json().catch(() => ({})));
  for (let attempt = 0; attempt < 20; attempt++) {
    const state = await data(await fetchImpl(`${API}/documents/${encodeURIComponent(document)}`,
      {headers: headers(token.accessToken, version)}));
    if (state.status === 'AVAILABLE') return document;
    if (state.status === 'PROCESSING_FAILED') throw new Error('LinkedIn document processing failed');
    await sleep(3000);
  }
  throw new Error('LinkedIn document processing did not complete in the review window');
}

async function uploadVideo(plan, token, version, fetchImpl, sleep) {
  const apiHeaders = {...headers(token.accessToken, version), 'Content-Type': 'application/json'};
  const initialized = await data(await fetchImpl(`${API}/videos?action=initializeUpload`, {method: 'POST', headers: apiHeaders,
    body: JSON.stringify({initializeUploadRequest: {owner: token.memberUrn, fileSizeBytes: fs.statSync(plan.media).size,
      uploadCaptions: Boolean(plan.captions), uploadThumbnail: true}})}));
  const info = initialized.value ?? {};
  if (!info.video || !Array.isArray(info.uploadInstructions) || !info.uploadInstructions.length || !info.thumbnailUploadUrl ||
      (plan.captions && !info.captionsUploadUrl)) throw new Error('LinkedIn video upload initialization is incomplete');
  const file = fs.openSync(plan.media, 'r');
  const partIds = [];
  try {
    for (const part of info.uploadInstructions) {
      const size = part.lastByte - part.firstByte + 1;
      if (!part.uploadUrl || !Number.isSafeInteger(size) || size <= 0 || size > 8 * 1024 * 1024) throw new Error('Invalid LinkedIn video upload part');
      const bytes = Buffer.alloc(size);
      if (fs.readSync(file, bytes, 0, size, part.firstByte) !== size) throw new Error('Video upload part ended early');
      const response = await fetchImpl(part.uploadUrl, {method: 'PUT', headers: {'Content-Type': 'application/octet-stream'}, body: bytes});
      if (!response.ok) throw responseError(response, await response.json().catch(() => ({})));
      const etag = response.headers.get('etag')?.replace(/^"|"$/g, '');
      if (!etag) throw new Error('LinkedIn video part returned no ETag');
      partIds.push(etag);
    }
  } finally { fs.closeSync(file); }
  const thumbnail = await fetchImpl(info.thumbnailUploadUrl, {method: 'PUT', headers: {'Content-Type': 'application/octet-stream', 'media-type-family': 'STILLIMAGE'}, body: fs.readFileSync(plan.cover)});
  if (!thumbnail.ok) throw responseError(thumbnail, await thumbnail.json().catch(() => ({})));
  if (plan.captions) {
    const form = new FormData();
    form.append('metadata', JSON.stringify({format: 'SRT', source: 'USER_PROVIDED',
      locale: {country: 'US', language: 'EN'}, transcriptType: 'CLOSED_CAPTION'}));
    form.append('file', new Blob([fs.readFileSync(plan.captions)], {type: 'text/plain'}), 'captions.srt');
    const captions = await fetchImpl(info.captionsUploadUrl, {method: 'POST', body: form});
    if (!captions.ok) throw responseError(captions, await captions.json().catch(() => ({})));
  }
  await data(await fetchImpl(`${API}/videos?action=finalizeUpload`, {method: 'POST', headers: apiHeaders,
    body: JSON.stringify({finalizeUploadRequest: {video: info.video, uploadToken: info.uploadToken ?? '', uploadedPartIds: partIds}})}));
  for (let attempt = 0; attempt < 20; attempt++) {
    const status = await data(await fetchImpl(`${API}/videos/${encodeURIComponent(info.video)}`, {headers: headers(token.accessToken, version)}));
    if (status.status === 'AVAILABLE') return info.video;
    if (status.status === 'PROCESSING_FAILED') throw new Error(`LinkedIn video processing failed: ${status.processingFailureReason ?? 'unknown'}`);
    await sleep(3000);
  }
  throw new Error('LinkedIn video processing did not complete in the review window');
}

export async function publishLinkedin(draft, workspace, options = {}, fetchImpl = fetch) {
  const plan = publicationPlan(draft);
  const previewFile = path.join(draft, 'linkedin-dry-run.json');
  if (!options.confirm) {
    // The separate publish request must refer to a package already shown in a dry run.
    save(previewFile, {fingerprint: plan.fingerprint, files: plan.files, preparedAt: new Date().toISOString()});
    return {dryRun: true, format: plan.format, copy: plan.copy, media: plan.media,
      cover: plan.cover, captions: plan.captions, altText: plan.altText, files: plan.files, fingerprint: plan.fingerprint};
  }
  if (!fs.existsSync(previewFile) || read(previewFile).fingerprint !== plan.fingerprint)
    throw new Error('Show a dry run of this exact LinkedIn package before confirmed publication');
  if (!String(options.authorizationNote ?? '').trim()) throw new Error('Confirmed LinkedIn publishing needs a separate authorization note');
  const receiptFile = path.join(draft, 'linkedin-receipt.json');
  const receipt = fs.existsSync(receiptFile) ? read(receiptFile) : {};
  if (receipt.postId) throw new Error(`LinkedIn post ${receipt.postId} already recorded`);
  if (receipt.postAttemptedAt) throw new Error('LinkedIn post call may have succeeded; reconcile the profile before retrying');
  if (receipt.fingerprint && receipt.fingerprint !== plan.fingerprint) throw new Error('Recorded LinkedIn upload differs from the approved package');
  const token = options.token ?? loadToken(workspace);
  const version = options.apiVersion ?? process.env.CONTENT_STUDIO_LINKEDIN_API_VERSION ?? '202610';
  const apiHeaders = {...headers(token.accessToken, version), 'Content-Type': 'application/json'};
  // Uploads may be retried before post creation; keep their URN to avoid redundant media uploads.
  let mediaUrn = receipt.mediaUrn ?? null;
  if (plan.media && !mediaUrn) {
    const sleep = options.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    mediaUrn = ['image', 'animated-image'].includes(plan.format) ? await uploadImage(plan, token, version, fetchImpl) :
      plan.format === 'carousel' ? await uploadDocument(plan, token, version, fetchImpl, sleep) :
        await uploadVideo(plan, token, version, fetchImpl, sleep);
    Object.assign(receipt, {fingerprint: plan.fingerprint, mediaUrn, mediaUploadedAt: new Date().toISOString()});
    save(receiptFile, receipt);
  }
  const body = {author: token.memberUrn, commentary: plan.copy, visibility: 'PUBLIC',
    distribution: {feedDistribution: 'MAIN_FEED', targetEntities: [], thirdPartyDistributionChannels: []},
    lifecycleState: 'PUBLISHED', isReshareDisabledByAuthor: false,
    ...(mediaUrn ? {content: {media: {id: mediaUrn,
      ...(['video', 'carousel'].includes(plan.format) ? {title: plan.title} : {}),
      ...(['image', 'animated-image'].includes(plan.format) && plan.altText ? {altText: plan.altText} : {})}}} : {})};
  Object.assign(receipt, {fingerprint: plan.fingerprint, postAttemptedAt: new Date().toISOString(),
    authorizationNote: options.authorizationNote.trim(), memberUrn: token.memberUrn});
  save(receiptFile, receipt);
  const response = await fetchImpl(`${API}/posts`, {method: 'POST', headers: apiHeaders, body: JSON.stringify(body)});
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    if ([400, 401, 403].includes(response.status)) {
      // These explicit rejections cannot have created a post; a later authorized retry is safe.
      delete receipt.postAttemptedAt;
      receipt.rejectedAt = new Date().toISOString();
      receipt.rejectionStatus = response.status;
      save(receiptFile, receipt);
    }
    throw responseError(response, errorBody);
  }
  const id = response.headers.get('x-restli-id');
  if (!id) throw new Error('LinkedIn returned no post ID; reconcile the profile before retrying');
  if (!/^urn:li:(ugcPost|share):[A-Za-z0-9_-]+$/.test(id)) throw new Error('LinkedIn returned an unexpected post ID; reconcile before retrying');
  Object.assign(receipt, {postId: id, publishedAt: new Date().toISOString(),
    url: `https://www.linkedin.com/feed/update/${id}/`});
  save(receiptFile, receipt);
  return {postId: id, url: receipt.url, format: plan.format};
}
