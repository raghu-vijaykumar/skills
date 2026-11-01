import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {parseArgs, runDigest} from '../index.mjs';

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'idea-digest-test-'));
  const sources = path.join(root, 'sources.yaml');
  fs.writeFileSync(sources, `settings:\n  timezone: UTC\n  lookbackDays: 7\n  limitPerSection: 0\ntopics:\n  - id: engineering\n    label: Engineering\n    sources:\n      - name: Working Feed\n        url: https://example.test/feed.xml\n      - name: Failed Feed\n        url: https://example.test/bad.xml\npapers:\n  enabled: false\n`);
  return {root, sources};
}
function cleanup(root) {
  if (!path.resolve(root).startsWith(path.resolve(os.tmpdir()) + path.sep)) throw new Error('Unsafe test cleanup');
  fs.rmSync(root, {recursive: true, force: true});
}
const rss = `<?xml version="1.0"?><rss version="2.0"><channel><title>Feed</title><item><title>How the cache works</title><link>https://example.test/article</link><pubDate>Sat, 01 Nov 2026 00:00:00 GMT</pubDate></item></channel></rss>`;

test('default digest writes dated JSON leads and leaves sent state untouched', async () => {
  const {root, sources} = fixture();
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return String(url).endsWith('bad.xml') ? new Response('down', {status: 503}) : new Response(rss, {status: 200});
  };
  try {
    const snapshot = await runDigest({workspace: root, sources, noPapers: true, noGithub: true, topics: [], days: 7});
    assert.equal(snapshot.count, 1);
    assert.equal(snapshot.items[0].title, 'How the cache works');
    assert.equal(snapshot.items[0].source, 'Working Feed');
    assert.equal(snapshot.items[0].publishedAt, '2026-11-01T00:00:00.000Z');
    assert.equal(snapshot.sourceFailures.length, 1);
    assert.ok(calls.every((url) => !url.includes('api.telegram.org')));
    assert.equal(fs.existsSync(path.join(root, 'analysis', 'digest', 'sent.json')), false);
    assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'analysis', 'digest', 'latest.json'))).count, 1);
  } finally { globalThis.fetch = original; cleanup(root); }
});

test('preview writes nothing and Telegram requires explicit credentials', async () => {
  const {root, sources} = fixture();
  const originalFetch = globalThis.fetch;
  const originalToken = process.env.TELEGRAM_BOT_TOKEN;
  const originalChat = process.env.TELEGRAM_CHAT_ID;
  delete process.env.TELEGRAM_BOT_TOKEN;
  delete process.env.TELEGRAM_CHAT_ID;
  globalThis.fetch = async () => new Response(rss, {status: 200});
  try {
    await runDigest({workspace: root, sources, noPapers: true, noGithub: true, topics: [], days: 7, preview: true});
    assert.equal(fs.existsSync(path.join(root, 'analysis', 'digest')), false);
    await assert.rejects(runDigest({workspace: root, sources, noPapers: true, noGithub: true, topics: [], days: 7, sendTelegram: true}), /requires TELEGRAM_BOT_TOKEN/);
    assert.throws(() => parseArgs(['--workspace', root, '--reset-sent']), /requires --send-telegram/);
    assert.throws(() => parseArgs(['--workspace', root, '--preview', '--send-telegram']), /Choose preview/);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalToken === undefined) delete process.env.TELEGRAM_BOT_TOKEN; else process.env.TELEGRAM_BOT_TOKEN = originalToken;
    if (originalChat === undefined) delete process.env.TELEGRAM_CHAT_ID; else process.env.TELEGRAM_CHAT_ID = originalChat;
    cleanup(root);
  }
});
