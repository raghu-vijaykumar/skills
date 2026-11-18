---
name: content-studio-social-linkedin-analytics
description: Analyze supplied personal LinkedIn post analytics and publication receipts without claiming a live collector.
---

# LinkedIn Analytics

Use the personal LinkedIn workspace and published post IDs from [LinkedIn Author](../author/SKILL.md). The current `content-studio linkedin` CLI records publication receipts but has no analytics-read command. The `w_member_social` publishing connection alone is not evidence that analytics access is available. Use an account export, a user-supplied Insights capture, or an authorized connected source when available; do not fabricate a live result.

For each post, record the source and observation time, reporting period, format, post URL, and only metrics actually present. Keep missing fields `null`. Compare posts by format and age, distinguish impressions from public reactions, and identify the uncertainty behind any recommendation. Use [the shared record structure](../../references/analytics.md). Store raw captures and derived reports in the personal content workspace, outside this repository. An analytics review never changes publication approval or triggers a new post.
