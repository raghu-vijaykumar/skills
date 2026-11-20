# Published Video Insights

One Markdown note per channel and one per verified published video. Agent-written interpretations stay distinct from measured evidence; raw analytics and comments stay in the channel workspace outside this repository.

**Status:** `Supported` means the skill manifest provides a runnable script. **Delivery timeline:** `No` means this read-only planning input does not render media. The source refresh writes owned reports and notes, not a draft or final video.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `prepare` | Supported | Verified archive and cached reports → channel and per-video `video-insights.md` | No | [Note contract](#note-contract) | Offline; cannot invent missing metrics or agent conclusions. |
| `refresh` | Supported | Authorized owned YouTube reports and bounded comments → cached reports, notes, source status | No | [Commands](#commands) | Existing collectors cover local archived metadata; old pruned IDs retain cached notes but cannot be freshly queried by those collectors. |
| `paths` | Supported | Verified published index → paths to the channel and selected per-video notes | No | [Commands](#commands) | A ledger-only ID is not verified publication evidence. |

## Commands

From the repository root:

```powershell
python content-studio/skills/content-studio-video/planning/video-insights/scripts/video_insights.py prepare --channel out-of-office
python content-studio/skills/content-studio-video/planning/video-insights/scripts/video_insights.py refresh --channel out-of-office --last 10 --comments-limit 100 --vtr-count 0
python content-studio/skills/content-studio-video/planning/video-insights/scripts/video_insights.py refresh --channel out-of-office --last 10 --comments-limit 100 --vtr-count 0 --reauthorize
python content-studio/skills/content-studio-video/planning/video-insights/scripts/video_insights.py paths --channel out-of-office --video VIDEOID
```

`--config` selects another channel-helper config. `refresh` invokes the existing `content.py analytics` and `content.py insights` commands. It uses their configured Google OAuth token for comments; an expired grant requires `--reauthorize` and the account owner's read-only consent in the browser. The wrapper attempts that consent once. If the configured client file was moved, the existing private token cache can supply its saved client pair. A report failure returns a nonzero exit code and writes `video-insights-source-status.json`; `prepare` still updates notes from whatever evidence is available. The comment collection stores text, ID, timestamp, likes and comment URL, without author names or profile IDs. It samples at most 500 top-level comments per video and does not claim to represent all feedback.

The wrapper expires its collected raw comment files after 30 days on `prepare` or `refresh`, in line with [YouTube's API data storage rules](https://developers.google.com/youtube/terms/developer-policies/). Refresh them before reusing older audience interpretations. Agent notes should paraphrase recurring themes, not retain comment text or commenter identities.

## Note contract

In a legacy channel such as Out of Office Mode:

```text
<channel>/analytics/video-insights.md
<channel>/analytics/<videoId>/video-insights.md
<channel>/analytics/published-index.json
<channel>/analytics/video-insights-source-status.json
```

Compact channels already using `analysis/analytics/` keep the same file names there. The script replaces only text between `VIDEO INSIGHTS: AUTO EVIDENCE` markers. If markers are missing or duplicated, it refuses to modify the file. An agent owns the prose sections and should cite the exact report and published video ID for each observation. The channel note should promote repeated patterns only after reviewing comparable videos and counterexamples. For a new edit, read the notes; the draft receives suggestions in its normal human-approved plan, not a copy of the insights history.

## Evidence note

Tests use synthetic channel metadata, metrics, comments, and note edits. No private channel data, credentials, comments, or media are committed here.
