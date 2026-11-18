# Implementation Plan: Script rhythm for Content Studio

**Spec:** [spec.md](spec.md) | **Branch:** `main`

## Design

- Keep one canonical, dependency-free Python rhythm analyzer. It accepts ordered cue IDs and text, with optional times and speaking-rate data, then returns structured advisory observations. It never rewrites text or judges whether a short line has a true story purpose.
- Integrate its results into the existing `voiceover-report.json` and readable Markdown without changing `pass`/`review`/`fail` status. Existing timing and scene-evidence checks remain authoritative.
- Provide a `--rhythm-only` path in the code-driven narration command. It parses the same authored phrases as synthesis, writes a report before synthesis, and does not generate speech. Normal narration also refreshes the report before its cache or synthesis path.
- Extend voiceover and narration-scoring guidance: short pivots may introduce a question, complication, decision, or payoff; long-form rhythm also uses scene and chapter progress and intentional natural-sound breaks.

## Constitution check

One canonical analyzer, portable inputs, source preservation, evidence-linked review, and matching tests/docs meet the current constitution. This feature ships no generated media or third-party Reel transcript.

## Verification

Run focused Python and Node tests, `npm run check:docs`, and a no-synthesis narration fixture. Review report contents and verify that existing validation outcomes do not change. Stage only this feature's files, inspect the staged diff, commit on `main`, push, and verify the remote head.
