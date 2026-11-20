---
name: content-studio-video-insights
description: Refresh and write evidence-linked Video Insights for a channel and its published videos, then use them to guide future edits.
---

# Published Video Insights

Use this skill when an editor asks what the channel's published archive teaches about a new video. The insight notes belong to the **published channel archive**, not a draft. Use the configured channel in `../../edit/clip-edit/config.json` and read the [channel helper](../../edit/clip-edit/references/channel-helper.md) and [measurement guidance](../ideagen/references/measurement.md).

Run `python <this-skill>/scripts/video_insights.py refresh --channel <slug> --last 10` to refresh available owned YouTube reports, collect up to 100 recent top-level comments per selected public video, and prepare the notes. `prepare` updates notes from cached reports without network access; `paths` lists the exact notes. Use `--comments-limit 0` when comments are not needed. An `invalid_grant` result requires `refresh --reauthorize` and the account owner's normal Google consent. The wrapper reuses `content.py analytics` and `content.py insights`; it does not create a second metrics store. A source failure is reported and cached evidence remains available.

The channel note is `<channel analytics root>/video-insights.md`. Each verified published video has `<channel analytics root>/<videoId>/video-insights.md`. The companion `published-index.json` retains previously verified IDs after local media pruning. A download ledger entry alone is not publication proof. Private, scheduled, and unverified videos do not receive published insight notes. Existing channel workspaces can keep analytics at the channel root; do not create a new `analysis/` folder merely for this skill, because the helper chooses its analytics path from that folder's presence.

The script owns only the marked **Measured evidence** sections. As the agent, read the linked metrics, retention curve, available comments, exact published video or a bounded segment, and creative metadata. Write substantive **Observations**, **Interpretation and limits**, and **Suggestions for future edits** in each video note. Record source video IDs, observation dates, timestamps, supporting metrics, and counterexamples. Paraphrase audience themes; do not copy comment text or commenter identities into durable notes. Update the channel note only with patterns supported by multiple relevant published videos, with sample size and uncertainty. Never infer intent or causality from a single dip or comment. If source media was pruned and is not locally available, label any visual interpretation unverified.

Before planning a new video or editing a supplied one, read the channel note and the most relevant published-video notes. Turn a supported finding into a bounded suggestion at the outline, rough-cut, narration, or package review checkpoint. The mandatory [workflow precheck](../../../content-studio-workflow/SKILL.md) still requires a human-approved plan before production edits; the approved timeline and exact-master review still govern delivery. Neither Video Insights nor a high-performing prior video authorizes automatic edits or publication. Do not write experiment or insight files under drafts.

See [the capability matrix and commands](README.md).
