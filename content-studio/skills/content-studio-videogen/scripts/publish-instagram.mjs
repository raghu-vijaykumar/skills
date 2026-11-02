// Instagram Reel publication keeps a checkpoint before every irreversible API call.
// A failed or ambiguous media_publish response must be reconciled, never retried blindly.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {sourceRevision} from '../../../scripts/source-revision.mjs';
import {selectMaster} from './publish-youtube.mjs';

const GRAPH = 'https://graph.facebook.com';
const PROFILE_VERSION = 1;
const MAX_BYTES = 1024 * 1024 * 1024;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const digest = async (file) => {
  const hash = createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
};

function readReceipt(file) {
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
}
function writeReceipt(file, receipt) {
  fs.writeFileSync(file, JSON.stringify(receipt, null, 2) + '\n');
}
function committedSource(cwd, draftDir) {
  return sourceRevision(cwd, draftDir);
}

export function instagramPlan(item) {
  const caption = String(item.value.publishing?.instagram?.caption ?? '').trim();
  if (!caption) throw new Error('publishing.instagram.caption is required');
  if (caption.length > 2200) throw new Error('Instagram caption exceeds 2200 characters');
  if ((caption.match(/#[\p{L}\p{N}_]+/gu) ?? []).length > 30) throw new Error('Instagram caption exceeds 30 hashtags');
  const id = item.value.video?.id ?? path.basename(item.dir);
  const render = selectMaster(item.dir, id);
  if (fs.statSync(render).size > MAX_BYTES) throw new Error('Instagram Reel exceeds 1 GB');
  return {id, caption, render};
}

function probe(file) {
  let output;
  try {
    output = execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
      'stream=width,height,avg_frame_rate:format=duration', '-of', 'json', file], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']});
  } catch { throw new Error('ffprobe is required to validate an Instagram Reel'); }
  const data = JSON.parse(output);
  const stream = data.streams?.[0];
  const duration = Number(data.format?.duration);
  const ratio = Number(stream?.width) / Number(stream?.height);
  const [numerator, denominator] = String(stream?.avg_frame_rate ?? '').split('/').map(Number);
  const fps = numerator / denominator;
  if (!Number.isFinite(duration) || duration < 3 || duration > 15 * 60) throw new Error('Instagram Reel must be 3 seconds to 15 minutes');
  if (!Number.isFinite(ratio) || Math.abs(ratio - 9 / 16) > 0.035) throw new Error('Instagram Reel master must be portrait 9:16');
  if (!Number.isFinite(fps) || fps < 23 || fps > 60) throw new Error('Instagram Reel must be 23-60 fps');
}

export function prepareReel(plan, config = {}) {
  probe(plan.render);
  const root = path.resolve(process.cwd(), config.workDir ?? 'tmp', 'publish', plan.id);
  fs.mkdirSync(root, {recursive: true});
  const output = path.join(root, 'instagram-upload.mp4');
  const cache = path.join(root, 'instagram-upload.json');
  const intermediate = path.join(root, 'instagram-upload.ts');
  const source = fs.statSync(plan.render);
  const signature = {profileVersion: PROFILE_VERSION, sourcePath: path.resolve(plan.render), sourceSize: source.size, sourceMtimeMs: source.mtimeMs};
  if (fs.existsSync(output) && fs.existsSync(cache)) {
    try {
      if (JSON.stringify(JSON.parse(fs.readFileSync(cache, 'utf8'))) === JSON.stringify(signature)) return output;
    } catch { /* A corrupt cache is rebuilt. */ }
  }
  // MPEG-TS strips Chrome's ICC side data before MP4 remux; the authored master is untouched.
  try {
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', plan.render, '-map_metadata', '-1', '-map_chapters', '-1',
      '-vf', 'scale=1080:1920:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
      '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
      '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
      '-g', '60', '-keyint_min', '60', '-sc_threshold', '0', '-bf', '2',
      '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2', '-sn', '-f', 'mpegts', intermediate],
    {stdio: ['ignore', 'pipe', 'pipe']});
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', intermediate, '-c', 'copy', '-movflags', '+faststart', output],
      {stdio: ['ignore', 'pipe', 'pipe']});
  } finally {
    fs.rmSync(intermediate, {force: true});
  }
  if (fs.statSync(output).size > MAX_BYTES) throw new Error('Prepared Instagram Reel exceeds 1 GB');
  fs.writeFileSync(cache, JSON.stringify(signature, null, 2) + '\n');
  return output;
}

function credentials(config) {
  const tokenFile = path.resolve(process.cwd(), config.publish?.instagram?.tokenFile ?? 'secrets/instagram-token.json');
  const stored = fs.existsSync(tokenFile) ? JSON.parse(fs.readFileSync(tokenFile, 'utf8')) : {};
  const token = stored.instagram ?? stored;
  const accessToken = process.env.IG_ACCESS_TOKEN ?? token.accessToken;
  const igUserId = process.env.IG_USER_ID ?? token.igUserId;
  if (!accessToken || !igUserId) throw new Error('Instagram credentials missing; set IG_ACCESS_TOKEN and IG_USER_ID or publish.instagram.tokenFile');
  return {accessToken, igUserId: String(igUserId), version: config.publish?.instagram?.apiVersion ?? process.env.IG_API_VERSION ?? 'v25.0'};
}

async function graphJson(response) {
  const raw = await response.text();
  let body;
  try { body = raw ? JSON.parse(raw) : {}; } catch { body = {raw}; }
  if (!response.ok || body.error) throw new Error(`Instagram Graph API ${response.status}: ${body.error?.message ?? body.raw ?? 'unknown error'}`);
  return body;
}
async function status(containerId, auth, fetchImpl) {
  const query = new URLSearchParams({fields: 'status_code,status', access_token: auth.accessToken});
  return graphJson(await fetchImpl(`${GRAPH}/${auth.version}/${containerId}?${query}`));
}
async function waitUntilReady(containerId, auth, fetchImpl, {intervalMs = 30_000, timeoutMs = 10 * 60_000, sleepImpl = sleep} = {}) {
  const start = Date.now();
  for (;;) {
    const result = await status(containerId, auth, fetchImpl);
    if (result.status_code === 'FINISHED') return;
    if (['ERROR', 'EXPIRED'].includes(result.status_code)) throw new Error(`Instagram container ${containerId}: ${result.status_code} ${result.status ?? ''}`.trim());
    if (Date.now() - start >= timeoutMs) throw new Error(`Instagram container ${containerId} did not finish within ${Math.round(timeoutMs / 1000)} seconds`);
    await sleepImpl(intervalMs);
  }
}

export async function publishInstagram(item, config, options = {}, fetchImpl = fetch) {
  if (options.at) throw new Error('Instagram does not support native scheduling; use YouTube --at or publish Instagram now');
  const plan = instagramPlan(item);
  const receiptFile = path.join(item.dir, 'draft.json');
  const receipt = readReceipt(receiptFile);
  if (!options.confirm) return {dryRun: true, platform: 'instagram', render: plan.render, caption: plan.caption,
    existingInstagramId: receipt.instagramId ?? null, pendingContainerId: receipt.instagramContainerId ?? null};
  if (receipt.instagramId) throw new Error(`Instagram media ${receipt.instagramId} is already recorded for this draft`);
  if (receipt.instagramPublishAttemptedAt) throw new Error('An Instagram publish call may have succeeded; reconcile the container in Instagram before retrying');
  if (receipt.instagramContainerId && !options.resume) throw new Error('An Instagram container is already recorded; use --resume');
  if (!receipt.instagramContainerId && options.resume) throw new Error('No Instagram container to resume');
  const renderSha256 = await digest(plan.render);
  if (receipt.instagramContainerId && (receipt.instagramRenderSha256 !== renderSha256 || receipt.instagramCaption !== plan.caption)) {
    throw new Error('Recorded Instagram container differs from current caption or master render');
  }
  const sourceCommit = receipt.instagramContainerId ? receipt.instagramSourceCommit : committedSource(process.cwd(), item.dir);
  const auth = credentials(config);
  const reelFile = (options.prepare ?? prepareReel)(plan, config);
  let containerId = receipt.instagramContainerId;
  if (!containerId) {
    const body = new URLSearchParams({media_type: 'REELS', upload_type: 'resumable', caption: plan.caption,
      share_to_feed: 'true', access_token: auth.accessToken});
    const created = await graphJson(await fetchImpl(`${GRAPH}/${auth.version}/${auth.igUserId}/media`, {method: 'POST', body}));
    if (!created.id || !created.uri) throw new Error('Instagram did not return a container ID and upload URI');
    const uri = new URL(created.uri);
    if (uri.protocol !== 'https:' || uri.hostname !== 'rupload.facebook.com' || uri.search || uri.hash) throw new Error('Instagram returned an unexpected upload URI');
    containerId = created.id;
    Object.assign(receipt, {instagramContainerId: containerId, instagramUploadUri: uri.toString(),
      instagramSourceCommit: sourceCommit, instagramRenderSha256: renderSha256, instagramCaption: plan.caption,
      instagramStatus: 'container-created'});
    writeReceipt(receiptFile, receipt);
  }
  if (receipt.instagramStatus !== 'ready') {
    // Meta has returned upload errors for containers that nevertheless finished processing.
    const current = await status(containerId, auth, fetchImpl);
    if (['ERROR', 'EXPIRED'].includes(current.status_code)) throw new Error(`Instagram container ${containerId}: ${current.status_code} ${current.status ?? ''}`.trim());
    if (current.status_code !== 'FINISHED') {
      const size = fs.statSync(reelFile).size;
      let uploadError = null;
      try {
        const response = await fetchImpl(receipt.instagramUploadUri, {method: 'POST',
          headers: {Authorization: `OAuth ${auth.accessToken}`, offset: '0', file_size: String(size),
            'Content-Type': 'application/octet-stream'}, body: fs.createReadStream(reelFile), duplex: 'half'});
        if (!response.ok) uploadError = `HTTP ${response.status}: ${(await response.text()).slice(0, 200)}`;
      } catch (error) { uploadError = error.message; }
      try { await waitUntilReady(containerId, auth, fetchImpl, options); }
      catch (error) { throw new Error(`${error.message}${uploadError ? `; upload response: ${uploadError}` : ''}`); }
    }
    receipt.instagramStatus = 'ready';
    writeReceipt(receiptFile, receipt);
  }
  // Persist uncertainty before the final request so a crash cannot cause a second public Reel.
  receipt.instagramPublishAttemptedAt = new Date().toISOString();
  writeReceipt(receiptFile, receipt);
  const published = await graphJson(await fetchImpl(`${GRAPH}/${auth.version}/${auth.igUserId}/media_publish`, {
    method: 'POST', body: new URLSearchParams({creation_id: containerId, access_token: auth.accessToken})}));
  if (!published.id) throw new Error('Instagram publish returned no media ID; reconcile before retrying');
  receipt.instagramId = published.id;
  receipt.instagramStatus = 'published';
  receipt.instagramPublishedAt = new Date().toISOString();
  writeReceipt(receiptFile, receipt);
  return {instagramId: published.id, status: 'published'};
}
