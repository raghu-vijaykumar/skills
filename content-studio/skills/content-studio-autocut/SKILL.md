---
name: content-studio-autocut
description: Create a reviewable, non-destructive rough cut from a folder of videos using transcript-aware speech selection, shot detection, quality signals, and a configurable story outline.
---

# Content Studio AutoCut

Run `python <this-skill>/scripts/autocut.py --folder <videos> --duration 12m --style travel-vlog --output <rough-cut>`. Requires FFmpeg and FFprobe; optionally supply `--transcripts <json>` with per-file timestamped speech segments. The default deterministic heuristic uses scene cuts, audio silence and duration; it does **not** claim to semantically understand landmarks, stories or visual content without externally supplied annotations. Supply `--annotations <json>` for segment relevance scores and descriptive reasons from a vision/LLM analysis stage. Do not fabricate semantics.

Produces `edit-decisions.json`, `timeline.otio` (OpenTimelineIO JSON schema), `review.html`, and `rough-cut.mp4`. Timeline and decisions are source-referenced and non-destructive. Each selected range carries source in/out timestamps and selection reasons. The review report is a proposal, not publishing approval. Source files are never changed.

For speech-heavy footage, use real timestamped transcript segments to preserve whole utterances; absent transcripts, treat selection as a technical rough assembly requiring manual story review. Export is standardized to 1920x1080, 30fps, H.264 SDR and AAC. Avoid claiming HDR metadata or Dolby Vision preservation. Use a new output folder, or `--force` to replace generated outputs.
