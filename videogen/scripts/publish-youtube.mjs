// Reusable YouTube publication with an ID-first retry boundary.
// A returned video ID is persisted before thumbnail/playlist work so retries
// cannot create duplicate uploads after a partial API failure.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';

const API = 'https://www.googleapis.com/youtube/v3';
const UPLOAD = 'https://www.googleapis.com/upload/youtube/v3';
const TOKEN = 'https://oauth2.googleapis.com/token';
const rangeRender = /-\d+(?:\.\d+)?-\d+(?:\.\d+)?\.mp4$/i;
async function sha256(file) {
  const hash = createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}

export function selectMaster(draftDir, id) {
  const direct = path.join(draftDir, 'video.mp4');
  if (fs.existsSync(direct)) return direct;
  const dir = path.join(draftDir, 'assets', 'generated', 'video');
  const candidates = fs.existsSync(dir) ? fs.readdirSync(dir).filter((name) =>
    name.startsWith(`${id}-`) && name.endsWith('.mp4') && !rangeRender.test(name) && !name.endsWith('.ig-upload.mp4')) : [];
  const shortSide = (name) => {
    const match = name.match(/-(\d+)x(\d+)-/);
    return match ? Math.min(Number(match[1]), Number(match[2])) : 0;
  };
  candidates.sort((a, b) => Number(shortSide(b) === 1440) - Number(shortSide(a) === 1440) ||
    shortSide(b) - shortSide(a) || a.localeCompare(b));
  if (!candidates.length) throw new Error(`${id}: no full-length MP4 master; render a delivery video first`);
  return path.join(dir, candidates[0]);
}

export function publicationPlan(item, config, options = {}) {
  const youtube = item.value.publishing?.youtube ?? {};
  const title = String(youtube.title ?? item.value.video?.title ?? '').trim();
  const description = String(youtube.description ?? item.value.video?.description ?? '').trimEnd();
  if (!title || title.length > 100 || !description) throw new Error('YouTube title (1-100 chars) and description are required');
  const render = selectMaster(item.dir, item.value.video?.id ?? path.basename(item.dir));
  const thumbnail = ['thumbnail.png', 'thumbnail.jpg', 'thumbnail.jpeg']
    .map((name) => path.join(item.dir, name)).find((file) => fs.existsSync(file));
  if (!thumbnail || fs.statSync(thumbnail).size > 2 * 1024 * 1024) throw new Error('A PNG/JPEG thumbnail at 2 MB or less is required in the draft');
  const authoredTitle = path.join(item.dir, 'title.txt');
  const authoredDescription = path.join(item.dir, 'description.txt');
  if (!fs.existsSync(authoredTitle) || fs.readFileSync(authoredTitle, 'utf8').trim() !== title ||
      !fs.existsSync(authoredDescription) || fs.readFileSync(authoredDescription, 'utf8').trimEnd() !== description) {
    throw new Error('Draft title.txt and description.txt must match publishing.youtube metadata exactly');
  }
  const publishAt = options.at ? new Date(options.at) : null;
  if (publishAt && (!Number.isFinite(publishAt.getTime()) || publishAt.getTime() <= Date.now())) throw new Error('--at needs a future ISO timestamp');
  return {title, description, tags: youtube.tags ?? [], playlist: youtube.playlist ?? null,
    render, thumbnail, publishAt: publishAt?.toISOString() ?? null,
    categoryId: String(config.publish?.youtube?.categoryId ?? '28')};
}

function credentials(cwd, config) {
  const settings = config.publish?.youtube ?? {};
  const clientFile = path.resolve(cwd, settings.clientFile ?? 'secrets/youtube-client.json');
  const tokenFile = path.resolve(cwd, settings.tokenFile ?? 'secrets/youtube-token.json');
  const client = fs.existsSync(clientFile) ? JSON.parse(fs.readFileSync(clientFile, 'utf8')) : {};
  const secret = client.installed ?? client.web ?? client;
  const token = fs.existsSync(tokenFile) ? JSON.parse(fs.readFileSync(tokenFile, 'utf8')) : {};
  const clientId = process.env.YT_CLIENT_ID ?? secret.client_id;
  const clientSecret = process.env.YT_CLIENT_SECRET ?? secret.client_secret;
  const refreshToken = process.env.YT_REFRESH_TOKEN ?? token.refreshToken;
  if (!clientId || !clientSecret || !refreshToken) throw new Error('YouTube OAuth credentials are incomplete; configure client/token files or YT_* env vars');
  return {clientId, clientSecret, refreshToken};
}

async function json(response) {
  const text = await response.text();
  let body;
  try { body = text ? JSON.parse(text) : {}; } catch { body = {raw: text}; }
  if (!response.ok) throw new Error(`YouTube API ${response.status}: ${body.error?.message ?? body.error_description ?? body.raw ?? 'unknown error'}`);
  return body;
}

async function accessToken(cwd, config, fetchImpl) {
  const auth = credentials(cwd, config);
  const response = await fetchImpl(TOKEN, {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({client_id: auth.clientId, client_secret: auth.clientSecret, refresh_token: auth.refreshToken, grant_type: 'refresh_token'})});
  const body = await json(response);
  if (!body.access_token) throw new Error('YouTube token response had no access token');
  return body.access_token;
}

async function upload(plan, token, fetchImpl) {
  const size = fs.statSync(plan.render).size;
  const resource = {snippet: {title: plan.title, description: plan.description, tags: plan.tags, categoryId: plan.categoryId},
    status: {privacyStatus: plan.publishAt ? 'private' : 'public', selfDeclaredMadeForKids: false,
      ...(plan.publishAt ? {publishAt: plan.publishAt} : {})}};
  const init = await fetchImpl(`${UPLOAD}/videos?uploadType=resumable&part=snippet,status`, {
    method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json; charset=UTF-8',
      'X-Upload-Content-Length': String(size), 'X-Upload-Content-Type': 'video/mp4'}, body: JSON.stringify(resource)});
  await json(init);
  const location = init.headers.get('location');
  if (!location) throw new Error('YouTube did not return a resumable upload URL');
  const response = await fetchImpl(location, {method: 'PUT', headers: {'Content-Type': 'video/mp4', 'Content-Length': String(size)},
    body: fs.createReadStream(plan.render), duplex: 'half'});
  const result = await json(response);
  if (!result.id) throw new Error('YouTube upload returned no video ID');
  return result.id;
}

async function setThumbnail(id, file, token, fetchImpl) {
  const mime = /\.jpe?g$/i.test(file) ? 'image/jpeg' : 'image/png';
  await json(await fetchImpl(`${UPLOAD}/thumbnails/set?videoId=${encodeURIComponent(id)}&uploadType=media`, {
    method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': mime}, body: fs.readFileSync(file)}));
}

async function addToPlaylist(id, title, token, fetchImpl) {
  let pageToken = null;
  let playlistId = null;
  do {
    const query = new URLSearchParams({part: 'id,snippet', mine: 'true', maxResults: '50'});
    if (pageToken) query.set('pageToken', pageToken);
    const body = await json(await fetchImpl(`${API}/playlists?${query}`, {headers: {Authorization: `Bearer ${token}`}}));
    playlistId = body.items?.find((item) => item.snippet?.title === title)?.id;
    pageToken = body.nextPageToken ?? null;
  } while (!playlistId && pageToken);
  if (!playlistId) {
    const body = await json(await fetchImpl(`${API}/playlists?part=snippet,status`, {
      method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'},
      body: JSON.stringify({snippet: {title}, status: {privacyStatus: 'public'}})}));
    playlistId = body.id;
  }
  if (!playlistId) throw new Error('Could not resolve YouTube playlist');
  await json(await fetchImpl(`${API}/playlistItems?part=snippet`, {
    method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'},
    body: JSON.stringify({snippet: {playlistId, resourceId: {kind: 'youtube#video', videoId: id}}})}));
}

function committedSource(cwd, draftDir) {
  const rel = path.relative(cwd, draftDir);
  const changed = execFileSync('git', ['-C', cwd, 'status', '--porcelain', '--', rel], {encoding: 'utf8'}).trim();
  if (changed) throw new Error('Commit draft source, title, description, and thumbnail before publishing');
  return execFileSync('git', ['-C', cwd, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim();
}

export async function publishYoutube(item, config, options = {}, fetchImpl = fetch) {
  const cwd = process.cwd();
  const plan = publicationPlan(item, config, options);
  if (!options.confirm) return {dryRun: true, title: plan.title, render: plan.render,
    thumbnail: plan.thumbnail, publishAt: plan.publishAt};
  const manifestPath = path.join(item.dir, 'draft.json');
  const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
  if (manifest.youtubeId && !options.resume) throw new Error(`${item.dir}: YouTube ID ${manifest.youtubeId} already recorded; use --resume for incomplete setup`);
  if (manifest.youtubeId && (manifest.title !== plan.title || manifest.description !== plan.description ||
      manifest.renderSha256 !== await sha256(plan.render))) throw new Error('Recorded upload differs from current title, description, or render; restore the uploaded inputs before resuming');
  const sourceCommit = manifest.youtubeId ? manifest.sourceCommit : committedSource(cwd, item.dir);
  const token = await accessToken(cwd, config, fetchImpl);
  const id = manifest.youtubeId ?? await upload(plan, token, fetchImpl);
  if (!manifest.youtubeId) {
    Object.assign(manifest, {sourceId: path.basename(item.dir), youtubeId: id, sourceCommit,
      renderSha256: await sha256(plan.render), thumbnailSha256: await sha256(plan.thumbnail),
      title: plan.title, description: plan.description, status: plan.publishAt ? 'scheduled' : 'uploaded',
      publishAt: plan.publishAt, uploadedAt: new Date().toISOString(), thumbnailSet: false,
      playlistSet: !plan.playlist});
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  }
  if (!manifest.thumbnailSet) {
    await setThumbnail(id, plan.thumbnail, token, fetchImpl);
    manifest.thumbnailSet = true;
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  }
  if (!manifest.playlistSet && plan.playlist) {
    await addToPlaylist(id, plan.playlist, token, fetchImpl);
    manifest.playlistSet = true;
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  }
  return {youtubeId: id, status: manifest.status, publishAt: manifest.publishAt};
}
