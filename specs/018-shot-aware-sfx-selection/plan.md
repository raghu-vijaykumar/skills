# Implementation Plan: Shot-aware SFX selection

**Branch**: `raghu/instagram-reel-sfx` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

## Summary

Extend the existing private stock library rather than creating another catalogue. Store an `sfx_profile` with a reviewed audible label, shot situation tags, and identification evidence. Add a deterministic selector that reads shot ranges and tags and writes a proposal JSON. Workflow binds the exact selector command to its approved precheck plan.

## Technical context

- Python CLI in `content-studio/skills/content-studio-video/stock-library/scripts/library.py`; JSON schema version 1 is preserved with optional `sfx_profile`.
- No new runtime dependencies or media transformations. Private source media is preserved.
- Focused `unittest` coverage for metadata, match/duration decisions, dialogue preservation, and rights gate.
- Reviewable output only; approved timeline cue and final mix are later Content Studio steps.

## Constitution check

One canonical library script and catalogue, portable shot manifest, tests and documentation for new CLI commands, no generated media in Git. All pass. Production catalogue mutation remains under the separate precheck gate.

## Interface

`describe-sfx --id --label --shot-tags --note` changes only optional sound profile metadata. `suggest-sfx --shots <JSON> --output <JSON> [--mode delivery|reference]` selects one best candidate per eligible shot based on exact tag overlap and full-duration fit. Default `delivery` requires `reuse_status=reusable` and `effect_review=passed`. Output includes matched tags, placement eligibility, and approval requirement; it does not modify any timeline.

## Production route

Profile the Reel draft and current private catalogue, present a plan with exact four description commands and a selector review command, obtain explicit approval, run and document the checklist, and verify hashes and README. Keep uncertain labels broad until the editor identifies them by ear.

## Production result

The editor approved precheck plan SHA-256 `e4005a68f7b8def762cc7bd602112fbc86e9b1b55eb2bdd3d63c20e53716ba88`. All four checklist steps passed. The source Reel and four imported effect files retained their SHA-256 hashes. E01, E02, and R05 have pending audible identities; R18 is confirmed laughter. All four retain unknown rights and reference-only status. A hypothetical tagged-shot manifest proposed only R18 in reference mode, with placement disallowed and no timeline change. The managed Content Studio installation is version 0.6.5.
