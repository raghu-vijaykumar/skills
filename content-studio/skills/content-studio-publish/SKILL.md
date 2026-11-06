---
name: content-studio-publish
description: Publish an approved Remotion or edited video to YouTube now, schedule it on YouTube, or publish an Instagram Reel now. Use only after human review and an explicit publication request.
---

# Content Studio Publish

Verify the current `content-studio-workflow` plan checklist is complete before package approval. Publishing still needs its separate explicit human authorization.

A publication candidate has a draft record, a validated full-length master at `<id>-final.mp4` (legacy layouts are still read), reviewed `title.txt` and `description.txt`, an approved `thumbnail.png` or JPEG for YouTube, a `creative.json` record (theme, style, format, renderer, choices), and package approval tied to the exact file hashes. Vlog drafts do not require a transcript or captions. If the draft has `music-selection.json`, include the matching `music-credits.txt` attribution in the description before approval. If `draft.json` marks the draft as a main lifecycle run (`"lifecycle": "main"`) or `lifecycle-checklist.json` exists, the approval and confirmed publish paths require every pre-publish checklist item to be `done` with evidence or `not_applicable` with a reason; see [the lifecycle checklist](../content-studio/references/lifecycle-checklist.md). After the user reviews the master, title, description, thumbnail, and music credits, record approval with `node <bundle>/scripts/cli.mjs approve --channel <slug> --draft <id> --note "<what was reviewed>"`. Commit the approved draft source when the channel is a Git repository. If any file changes, obtain fresh approval. Preview with `node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id>`. For a configured Remotion project, `npx videogen publish <id>` remains a compatible route.

After explicit human authorization, add `--confirm` for YouTube now, `--platform instagram --confirm` for Instagram now, or `--at <future ISO timestamp with offset> --confirm` for native YouTube scheduling. Instagram has no scheduling path. Read [publishing rules](../../skills/content-studio-videogen/references/publishing.md). Keep receipts and platform IDs in the draft record; reconcile uncertain API responses before retrying. Scheduled and private uploads remain drafts until a public backup is verified.
