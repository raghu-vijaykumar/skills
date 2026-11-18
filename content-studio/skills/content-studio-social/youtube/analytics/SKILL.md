---
name: content-studio-social-youtube-analytics
description: Refresh and interpret owned YouTube channel analytics for Content Studio videos and ideas.
---

# YouTube Analytics

Use the existing owned-channel collector; this skill does not create a parallel analytics store. For a configured channel, run `python <bundle>/skills/content-studio-video/edit/clip-edit/scripts/content.py insights --channel <slug> --refresh --vtr-count 20`. For a bounded video report, run `python <bundle>/skills/content-studio-video/edit/clip-edit/scripts/content.py analytics --channel <slug> --last 5` or select `--video <id>`. Read the resulting channel `analytics/` records and `analysis/analytics/insights.json` when present. If authorization or a Studio measurement is unavailable, report that field as unavailable.

Apply [YouTube measurement guidance](../../../content-studio-video/planning/ideagen/references/measurement.md) and [the shared record structure](../../references/analytics.md). Keep owned Analytics and Studio numbers distinct from [public competitor observations](../../../content-studio-video/planning/ideagen/SKILL.md). Compare like formats and similar ages, include collection time and sample size, and frame any creative recommendation as an experiment. For new ideas, hand the result to [video ideagen](../../../content-studio-video/planning/ideagen/SKILL.md).
