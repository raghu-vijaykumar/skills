# Feature Specification: Earshot SFX in Content Studio

**Created:** 2026-11-18
**Status:** Implemented; bank listening review remains pending
**Branch:** `main`

## User outcomes

1. A clean Content Studio checkout contains the 252 effects from pinned Earshot commit `4ac3d2ac2b151e1c23376f9ce7f3047a17050013` as playable, catalogued WAVs. Each records source, license, hash, family, timing, and technical audit. Audit failures and unreviewed sounds cannot enter an approved final.
2. An editor can generate original forge sounds or fit user-provided recordings, retain the recipe and derivative rights, audition candidates, and approve eligible sounds for reuse. Recording licenses govern whether fitted outputs may ship in Git.
3. An agent can inspect a supplied edit or authored Remotion scene plan, identify timecoded events with evidence and original audio context, and propose a sound or no effect. Ambiguous visual meaning, dialogue, and meaningful natural sound remain unsounded.
4. Candidate cues become pending edited-video timeline or Remotion SFX declarations. A bounded picture-and-sound preview supports human review. Final export requires the existing production plan, cue, timeline, and exact-output gates.
5. For an audio-only change to an already edited HDR/Dolby Vision video, the final route copies coded picture packets, encodes mixed audio once, and refuses delivery if packet identity or color/Dolby metadata cannot be verified.

## Constraints and compatibility

- Earshot is a pinned build tool, not a vendored repository or required runtime for using the shipped WAVs.
- Existing unknown-rights Reel SFX stay Git-ignored and reference-only.
- The user explicitly authorizes shipped Earshot WAVs in Git as an exception to the constitution's usual generated-media exclusion. Review evidence, caches, and candidate media remain local.
- Automatic means evidence-backed **proposals and previews**, never automatic human approval or publication.
- Edited video understanding uses sampled frames and audio evidence; a reviewer must verify action semantics. Code-driven scene state changes are the authoritative event source.
