# Implementation Plan: Earshot SFX in Content Studio

**Spec:** [spec.md](spec.md) | **Branch:** `main`

## Design

- Extend the stock library's schema-1 entries with optional `origin` metadata: pinned bank ID/version, rights, audit, cue roles, measured sync points, and review status. Preserve the existing Reel entries and CLI behavior.
- Add one canonical audio/SFX skill. Its importer renders all bank IDs with pinned Earshot source, writes 24-bit WAVs and an audition gallery, and makes an idempotent catalogue update. Forge/fit candidates remain pending; adoption records recipe and source hashes.
- Add a route-neutral event manifest with source hash, time, type, confidence, audio context, and visual evidence. Edited analysis finds cut and motion-peak frame bursts plus quiet windows; an agent checks meaning. Remotion analysis reads authored state changes. A deterministic selector ranks audited sounds, measures an optional separate music bed, and includes an explicit no-effect result.
- Export proposal cues into an immutable timeline revision input or Remotion `MediaClip` JSON. The canonical Remotion entry mounts cues automatically; final validation binds them to current catalogue listening decisions. Keep cues pending until listening and exact cue approval. SDR uses the existing timeline mixer; the audio-only preserve route maps source video packets without video filters and verifies packet payloads and HDR/Dolby metadata before delivery.

## Constitution check

Canonical skill ownership, source preservation, evidence-backed review, portable paths, tests, and documentation are retained. The tracked Earshot WAV bank is the user's explicit exception to the ordinary generated-media rule. No reference-only recordings or review caches are committed.

## Verification

Check import count, hashes, audit gates, gallery, and Git ignore behavior. Exercise edited and Remotion events plus dialogue/uncertainty/collision cases. Render SDR and HLG audio-only fixtures, verify their audio and picture packet identities, and ensure mismatches fail closed. Run focused tests and documentation gates, inspect final evidence, then commit and push only feature files.
