#!/usr/bin/env node
// Source discovery belongs to the idea skill. JSON is the default; delivery is explicit.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {loadSecrets, loadSources, requireTelegram} from './lib/config.mjs';
import {fetchFeed} from './lib/rss.mjs';
import {fetchSitemap, scrapeSource} from './lib/scrape.mjs';
import {fetchNewRepos, fetchTrending} from './lib/github.mjs';
import {collectPapers} from './lib/papers.mjs';
import {buildMessage, countItems, splitMessage} from './lib/format.mjs';
import {applyLimit} from './lib/util.mjs';
import {renderPretty} from './lib/pretty.mjs';
import {sendMessageParts} from './lib/telegram.mjs';
import {loadSentKeys, saveSentKeys, sentFile} from './lib/state.mjs';

const HELP = `Video idea digest: collect dated source leads for a channel workspace.

Usage: node <skill>/digest/index.mjs --workspace <content-repo> [options]

Default: write analysis/digest/latest.json; send nothing.
  --days <n>              Lookback window (default from sources.yaml)
  --since YYYY-MM-DD       Start date instead of --days
  --topic <id,...>         Only these source groups
  --limit <n>             Items per section (0 = no limit)
  --no-feeds              Skip RSS, scraped pages, and sitemaps
  --no-papers             Skip viral papers
  --no-github             Skip GitHub sections
  --sources <yaml>        Override the skill's source catalog
  --out <json>            JSON output path (relative to workspace)
  --preview, --dry-run    Readable preview; no file or message written
  --raw                   With --preview, show Telegram HTML
  --send-telegram         Explicitly send and update per-channel sent history
  --reset-sent            With --send-telegram, clear sent history first
  --help                  Show this help`;

export function parseArgs(argv) {
  const args = {topics: []};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    const value = () => {
      const next = argv[++i];
      if (!next || next.startsWith('--')) throw new Error(`${token} needs a value`);
      return next;
    };
    switch (token) {
      case '--workspace': args.workspace = value(); break;
      case '--days': args.days = Number(value()); break;
      case '--since': args.since = value(); break;
      case '--limit': args.limit = Number(value()); break;
      case '--topic': args.topics.push(...value().split(',').map((x) => x.trim()).filter(Boolean)); break;
      case '--sources': args.sources = value(); break;
      case '--out': args.out = value(); break;
      case '--no-feeds': args.noFeeds = true; break;
      case '--no-papers': args.noPapers = true; break;
      case '--no-github': args.noGithub = true; break;
      case '--preview': case '--dry-run': args.preview = true; break;
      case '--raw': args.raw = true; break;
      case '--json': break; // Explicit spelling for the default mode.
      case '--send-telegram': args.sendTelegram = true; break;
      case '--reset-sent': args.resetSent = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`Unknown option: ${token}`);
    }
  }
  if (args.help) return args;
  if (!args.workspace) throw new Error('--workspace is required');
  if (args.days !== undefined && (!Number.isFinite(args.days) || args.days <= 0)) throw new Error('--days must be positive');
  if (args.limit !== undefined && (!Number.isInteger(args.limit) || args.limit < 0)) throw new Error('--limit must be a nonnegative integer');
  if (args.since && !/^\d{4}-\d{2}-\d{2}$/.test(args.since)) throw new Error('--since must be YYYY-MM-DD');
  if (args.preview && args.sendTelegram) throw new Error('Choose preview or Telegram delivery');
  if (args.resetSent && !args.sendTelegram) throw new Error('--reset-sent requires --send-telegram');
  if (args.raw && !args.preview) throw new Error('--raw requires --preview');
  return args;
}

function normalizedKey(item) {
  const arxiv = item.arxivId ?? (String(item.url ?? '').match(/arxiv\.org\/(?:abs|pdf)\/([0-9]{4}\.[0-9]{4,5})/i) ?? [])[1];
  if (arxiv) return `arxiv:${arxiv}`;
  try { const url = new URL(item.url); url.hash = ''; return url.toString().replace(/\/$/, '').toLowerCase(); }
  catch { return String(item.url ?? item.title).trim().toLowerCase(); }
}
function sourceFetcher(source) {
  return source.type === 'scrape' ? scrapeSource : source.type === 'sitemap' ? fetchSitemap : fetchFeed;
}
function iso(value) {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isFinite(date.getTime()) ? date.toISOString() : null;
}
function lead(item, kind, topic, observedAt) {
  return {
    kind, topic, title: item.title ?? item.fullName ?? '', url: item.url,
    source: item.source ?? (kind === 'repo' ? 'GitHub' : ''),
    publishedAt: iso(item.published ?? item.createdAt), observedAt,
    ...(item.metric ? {signal: item.metric} : {}),
    ...(item.starsToday != null ? {starsToday: item.starsToday} : {}),
    ...(item.stars != null ? {stars: item.stars} : {}),
    ...(item.description ? {description: item.description} : {}),
    ...(item.arxivId ? {arxivId: item.arxivId} : {}),
  };
}
function uniqueLeads(sections, papers, github, observedAt) {
  const all = [
    ...papers.map((item) => lead(item, 'paper', 'research', observedAt)),
    ...sections.flatMap(({topic, items}) => items.map((item) => lead(item, 'article', topic.id, observedAt))),
    ...(github?.trending ?? []).map((item) => lead(item, 'repo', 'github-trending', observedAt)),
    ...(github?.newRepos ?? []).map((item) => lead(item, 'repo', 'github-new', observedAt)),
  ];
  const seen = new Set();
  return all.filter((item) => {
    if (!item.title || !item.url) return false;
    const key = normalizedKey(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export async function runDigest(args) {
  const workspace = path.resolve(args.workspace);
  if (!fs.existsSync(workspace) || !fs.statSync(workspace).isDirectory()) throw new Error(`Workspace not found: ${workspace}`);
  const {settings, topics, papers: paperConfig} = loadSources(args.sources && path.resolve(args.sources));
  const secrets = loadSecrets(workspace);
  if (args.sendTelegram) requireTelegram(secrets);
  const days = args.days ?? settings.lookbackDays;
  const since = args.since ? new Date(`${args.since}T00:00:00Z`) : new Date(Date.now() - days * 86_400_000);
  if (!Number.isFinite(since.getTime())) throw new Error('Invalid sweep date');
  const selected = args.topics?.length ? topics.filter((topic) => args.topics.includes(topic.id)) : topics;
  const missing = (args.topics ?? []).filter((id) => !topics.some((topic) => topic.id === id));
  if (missing.length) throw new Error(`Unknown topic(s): ${missing.join(', ')}`);
  const limit = args.limit ?? settings.limitPerSection;
  const jobs = args.noFeeds ? [] : selected.flatMap((topic) => topic.sources.map((source) => ({topic, source})));
  const settled = await Promise.allSettled(jobs.map(({source}) => sourceFetcher(source)(source, {since})));
  const sections = selected.map((topic) => ({topic, items: []}));
  const sourceFailures = [];
  settled.forEach((result, index) => {
    const {topic, source} = jobs[index];
    if (result.status === 'fulfilled') sections.find((section) => section.topic.id === topic.id).items.push(...result.value);
    else sourceFailures.push({source: source.name, topic: topic.id, error: String(result.reason?.message ?? result.reason)});
  });
  for (const section of sections) {
    section.items.sort((a, b) => (b.published?.getTime() ?? 0) - (a.published?.getTime() ?? 0));
    section.items = applyLimit(section.items, limit);
  }
  let papers = args.noPapers || !paperConfig.enabled ? [] : await collectPapers({config: {...paperConfig, limit: args.limit ?? paperConfig.limit}, since, failures: sourceFailures});
  let github = null;
  if (!args.noGithub) {
    const [trending, newRepos] = await Promise.all([
      fetchTrending({limit, since: 'daily'}).catch((error) => { sourceFailures.push({source: 'GitHub Trending', topic: 'github', error: error.message}); return []; }),
      fetchNewRepos({since, token: secrets.githubToken, limit}).catch((error) => { sourceFailures.push({source: 'GitHub New', topic: 'github', error: error.message}); return []; }),
    ]);
    github = {trending, newRepos};
  }
  // Give richer paper entries priority when the same link appears in a feed.
  const seen = new Set();
  const keep = (item) => { const key = normalizedKey(item); if (seen.has(key)) return false; seen.add(key); return true; };
  papers = papers.filter(keep);
  for (const section of sections) section.items = section.items.filter(keep);
  if (github) { github.trending = github.trending.filter(keep); github.newRepos = github.newRepos.filter(keep); }
  const generatedAt = new Date().toISOString();
  const items = uniqueLeads(sections, papers, github, generatedAt);
  const snapshot = {schemaVersion: 1, generatedAt, since: since.toISOString(), feedSourceCount: jobs.length,
    sourceFailures, count: items.length, items};
  if (args.preview) {
    const message = buildMessage({settings, sections, papers, github, since});
    for (const chunk of splitMessage(message)) console.log(args.raw ? chunk : renderPretty(chunk));
    console.log(`Previewed ${items.length} lead(s); nothing sent or saved.`);
    return snapshot;
  }
  if (args.sendTelegram) {
    const file = sentFile(workspace);
    const sent = args.resetSent ? new Set() : loadSentKeys(file);
    if (args.resetSent) saveSentKeys(sent, file);
    const keep = (item) => !sent.has(normalizedKey(item));
    const toSend = sections.map(({topic, items}) => ({topic, items: items.filter(keep)}));
    const paperSend = papers.filter(keep);
    const githubSend = github && {trending: github.trending.filter(keep), newRepos: github.newRepos.filter(keep)};
    const total = countItems(toSend, paperSend, githubSend);
    if (!total) { console.log('No unsent items in this window.'); return snapshot; }
    const chunks = splitMessage(buildMessage({settings, sections: toSend, papers: paperSend, github: githubSend, since}));
    await sendMessageParts({token: secrets.telegramBotToken, chatId: secrets.telegramChatId, chunks});
    for (const item of [...paperSend, ...toSend.flatMap((section) => section.items), ...(githubSend?.trending ?? []), ...(githubSend?.newRepos ?? [])]) sent.add(normalizedKey(item));
    saveSentKeys(sent, file);
    console.log(`Sent ${chunks.length} Telegram message(s) with ${total} item(s).`);
    return snapshot;
  }
  const out = path.resolve(workspace, args.out ?? 'analysis/digest/latest.json');
  if (!out.startsWith(workspace + path.sep)) throw new Error('--out must stay inside the channel workspace');
  fs.mkdirSync(path.dirname(out), {recursive: true});
  fs.writeFileSync(out, JSON.stringify(snapshot, null, 2) + '\n');
  console.log(`Saved ${items.length} lead(s) to ${out}; ${sourceFailures.length} source(s) failed; nothing sent.`);
  return snapshot;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help) console.log(HELP);
    else await runDigest(args);
  } catch (error) {
    console.error(`idea-digest: ${error.message}`);
    process.exitCode = 1;
  }
}
