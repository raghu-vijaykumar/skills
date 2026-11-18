# Implementation Plan: Complete headless Blender capability roadmap

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Advance the 94-entry catalog from guidance to evidence-backed routes within the existing video animation code. Build the shared planner, resumable renderer, scoring gate, craft modules, authored scene recipes, and export verifiers in dependency order. Keep every status and README GIF tied to scored, exact-output evidence.

## Technical context and design

- Python 3 and Blender 5.3 own trusted `make_scene(spec, spec_dir)` builders; FFmpeg/FFprobe validate MP4 and GIF output. Existing videogen scene and asset manifests own video composition handoff.
- `animation/blender/capabilities.json` is the single 94-entry registry. `catalog.py` validates the pinned source, dependencies, route, status, scored GIF, and review record before generating the README table.
- The scene-aware style planner adds a Blender selection with subject, visual style, builder when supported, and `needs_builder` for missing implementations. Explicit Blender IDs override inference; production precheck carries the proposal to human approval.
- A shot specification records object and beat IDs, asset provenance, timing, camera, render profile, and required review states. Preview and full render load the same builder. Long renders write an input-hashed frame-batch manifest, durable log, completion marker, and recoverable frame sequence; final MP4 assembly probes the exact delivered media.
- Each full candidate receives five 0–5 editorial scores and technical results. The score record retains rejected candidates. Only the best passing candidate's optimized GIF is committed, and the catalog refuses a `Rendered` claim if its winner is absent or changed. Scores are editorial assessments, not audience metrics or production approval.
- Reusable primitives and original benchmark assets implement asset craft and technical routes first, then 31 distinct visual treatments, 23 setting or genre recipes plus the era route, and export and QA routes. Structural skills get mesh, UV, rig, simulation, or reimport checks in addition to moving evidence.

## Constitution check

- The existing animation skill owns the canonical implementation and is portable across content projects.
- Rendered review and exact output checks precede status advancement.
- Production edit approval and separate publication authorization remain in the Content Studio workflow.
- Requested optimized GIFs are committed evidence; large renders and private media remain outside Git.

## Verification and release

For each completed route, run focused Python tests, bounded Blender previews, full-shot or frame-batch validation, FFprobe and hash checks, scorebook verification, visual and structural review, `npm run check:docs`, `npm run check:capabilities`, and the relevant videogen tests. Review the staged diff, commit only the logical slice on `main`, push, and verify the remote. A failing pre-existing gate is tracked and resolved separately rather than silently skipped.
