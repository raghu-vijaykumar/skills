# Implementation Plan: Published Video Insights

**Branch**: `main` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

## Summary

Add a canonical Video Insights planning skill. Its wrapper reuses owned YouTube analytics commands, collects bounded comments with the existing read-only OAuth scope, and prepares Markdown notes with replaceable measured evidence and preserved agent prose.

## Technical Context

- **Language**: Python 3 standard library and Markdown.
- **Storage**: Existing channel analytics root: `video-insights.md` for the channel, `<videoId>/video-insights.md` per video, plus machine records for the index and comments.
- **Input**: Configured archive metadata, prior dataset and index, metrics, retention, optional authorized comments.
- **Testing**: Python unit tests, skill discovery, capability matrix, documentation checks.
- **Constraints**: No live channel writes in repository tests; no draft insight state; no automatic production or publication approval.

## Constitution Check

The skill is canonical, reuses the analytics store, accepts configured channel paths, preserves authored notes, and adds tests and documentation for the public command. No exception is needed.

## Design

1. Build a durable published index from current public archive metadata and prior verified index records. Do not treat the download ledger or an old analytics dataset alone as publication proof.
2. Use bounded auto-evidence markers in Markdown. Refuse malformed markers.
3. `prepare` is offline and idempotent. `refresh` calls existing analytics commands, optionally reads YouTube comment threads, records source status, then prepares notes.
4. The agent writes substantive insights after inspecting evidence. Planning and workflow skills read relevant notes and propose changes through existing approvals.

## Project Structure

```text
content-studio/skills/content-studio-video/planning/video-insights/
  SKILL.md README.md methods.json
  scripts/video_insights.py
  tests/test_video_insights.py
specs/040-published-video-insights/
  spec.md plan.md tasks.md
```

## Post-design constitution check

Archive identity is separate from drafts, raw metrics stay in the existing store, report gaps are explicit, and production approval remains unchanged.
