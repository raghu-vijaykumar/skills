# Idea digest

The bundled collector at `content-studio-ideas/digest/index.mjs` gathers recent leads from the skill's curated [source catalog](../digest/sources.yaml): RSS/Atom, official engineering blogs, scraped listings, sitemaps, viral papers, and GitHub. It is a discovery index. A headline, popularity count, or undated item does not establish a technical claim; open the original paper, spec, release note, or engineering write-up before adding a candidate to a brief.

Install its locked Node dependencies once in the skill folder:

```powershell
npm ci --prefix <content-studio-ideas-skill>/digest
```

Run it for a channel workspace (the default writes JSON and sends nothing):

```powershell
node <content-studio-ideas-skill>/digest/index.mjs --workspace C:\workspace\content\revise-labs --days 7 --limit 8
```

Read `analysis/digest/latest.json` in that channel workspace. Each item has a `kind`, topic, title, source, URL, `publishedAt` when known, and `observedAt`. The JSON also lists source failures. Re-run if the snapshot is stale, and do not treat a failed source as a negative result. `--topic systems,engineering`, `--no-papers`, and `--no-github` narrow the sweep; `--sources <yaml>` selects another catalog. `--preview` (or `--dry-run`) prints a readable view without writing. `--out <path>` chooses another JSON path under the workspace.

When creating a draft, pass that exact snapshot to `plan.py --digest-json <path>`. The planner adds up to twelve balanced leads under **Digest leads (unverified)** in `research.md`. Verify primary sources and dates, then score candidates using the normal idea-engine gates. The generated list is a starting pool, never the final research.

Telegram delivery is separate and only for an explicit request:

```powershell
node <content-studio-ideas-skill>/digest/index.mjs --workspace <channel-root> --days 1 --send-telegram
```

Put `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the environment or an ignored `<channel-root>/code/secrets/digest.env`; `GITHUB_TOKEN` is optional. Telegram sent-item history is `<channel-root>/analysis/digest/sent.json`. JSON and preview modes do not read or change sent history. The skill must not send Telegram messages merely because it is researching an idea.
