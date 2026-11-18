---
name: content-studio-social-linkedin-publish
description: Publish an exact approved personal LinkedIn package through the Content Studio dry run and explicit confirmation gates.
---

# LinkedIn Publish

Use the reviewed draft created by [LinkedIn Author](../author/SKILL.md). The existing `content-studio linkedin` CLI owns OAuth, media upload, the versioned Posts API and receipts; this leaf adds no second publisher.

Run `content-studio linkedin resume --draft <id>` and require `approved: final`. Show `content-studio linkedin publish --draft <id>` to record the dry run with exact copy and file hashes. Only after a separate explicit instruction to publish that specific package call `content-studio linkedin publish --draft <id> --confirm --authorization-note "<user authorization>"`. A changed package requires renewed review and dry run. If access is unavailable or a post response is uncertain, leave the package intact and reconcile before any retry. Read [the author workflow](../author/references/workflow.md) for workspace and connection details.
