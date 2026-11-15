# Implementation Plan: Idea to authored explainer

**Branch**: `main` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Extend the existing Content Studio idea planner and videogen scaffold/check/render path. Use a portable Core Explainer scene-plan contract and Remotion runtime. Keep authored pilot projects and large renders outside this package.

## Technical context

Node 22, TypeScript, React/Remotion, Python 3; JSON scene and asset manifests; Node tests and real Remotion render checks. The renderer remains project driven. No Blender dependency. Full output is 30 fps portrait or landscape MP4.

## Constitution check

One canonical source in `content-studio/`; no project path in runtime; public CLI and contract changes have tests and docs; rendered evidence required; no generated media committed. These gates must also pass after implementation.

## Structure

- `planning/ideagen/scripts/plan.py`: optional channel neutral draft.
- `planning/styles/scripts/style_engine.py`: Core Explainer treatment.
- `animation/videogen/scripts/`: scaffold and scene-plan validation.
- `animation/videogen/runtime/`: reusable visual scene components.
- `C:\workspace\content\motion-lab\authored-project`: private pilots and evidence.

## Research decisions

- The private reel is observation-only; no source-derived media enters compositions.
- Use Remotion with authored SVG/CSS interfaces and dimensional motion, plus newly generated transparent artwork where a hero object or presenter needs more detail. Keep the procedural presenter fallback for projects without artwork.
- Use official product documentation for technical claims; mark illustrative sequences.
- Preserve mandatory precheck evidence and user-approved plan; the user explicitly waived discretionary approval pauses for this test.
