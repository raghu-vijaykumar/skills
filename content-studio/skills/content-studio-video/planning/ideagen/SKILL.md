---
name: content-studio-video-ideagen
description: Find and research a short or long video idea using a channel's own analytics, curated digest, and public comparison videos. Use before creating a draft or when reviewing which style experiment to try next.
---

# Content Studio Ideas

Choose a channel from `content-studio-videoedit/config.json` and its ignored local override. Refresh that channel's owned analytics with `python <bundle>/skills/content-studio-videoedit/scripts/content.py insights --channel <slug> --refresh --vtr-count 20`. Read its `analysis/analytics/insights.json`, dataset and retention report; note unavailable CTR, VTR, or retention explicitly. Use [measurement guidance](references/measurement.md) to turn the data into reviewable recommendations.

Run the bundled [digest](references/digest.md) for dated leads, and use agentic web research to check primary sources. Find public comparison videos relevant to this topic, then collect their observable statistics with `python <bundle>/skills/content-studio-videoedit/scripts/content.py competitors --channel <slug> --topic "<topic>"`. Public views, likes, comments, publication dates, and titles are comparison signals; do not infer private CTR, VTR, or retention. Record source URLs and collection time.

Score candidate topics against this channel's audience, format, packaging, mechanism, evidence, and production effort. Propose one idea with the runner-up and the observed reason for the choice. Treat a small channel or small style cohort as uncertain. Do not promise virality.

Use `python <this-skill>/scripts/plan.py --channel <slug> --name "<idea>" --kind short|long --digest-json <channel-root>/analysis/digest/latest.json` after topic selection. The planner creates one editable draft and marks digest leads unverified. Use `content-studio-styles` to inspect available treatments, then record theme, style, and creative experiment in its brief. Changes to shared style presets require human review. For production, invoke `content-studio-videogen` or `content-studio-videopreprocess`; publishing and archive are separate skills.
