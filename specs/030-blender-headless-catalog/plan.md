# Implementation Plan: Blender headless capability catalog

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Index the upstream 94 skill names in the existing Content Studio video animation skill, adapt its useful craft guidance, and render three programmatic example scenes through the existing preview interface and a shared full-shot command. Generate the root README catalog and embed three optimized GIFs built from reviewed outputs.

## Technical context

- Python 3 with Blender 5.3 `bpy` for headless scene creation and render; Node 22 for repository checks.
- The existing engineering-3d `headless_preview.py` accepts project `make_scene(spec, spec_dir)` builders.
- FFmpeg builds GIFs from reviewed shot MP4s. Large renders and `.blend` files stay outside Git; requested GIFs are committed.
- Link to upstream files at an immutable commit; keep adapted instructions and render code in `content-studio-video/animation`.

## Design

1. Pin upstream commit `904f095d8f36a6e72adaebb08d07f884a074743d` as the catalog reference, with MIT attribution. A local category map and catalog script validate 94 unique IDs and produce the README table.
2. Extend the existing video animation skill with Blender craft guidance and method entries. The catalog labels skills as guidance; the three example routes have separate rendered evidence.
3. Add a full-shot runner that imports the same builder used by `headless_preview.py`, validates the scene and output, and records an editable `.blend`, MP4, input hashes, Blender version, and media facts.
4. Build original procedural scenes for a moving clamp, cel-shaded waving character, and camera-moving corridor. Review initial/action/result frames and whole motion at delivery size before converting exact MP4s into GIFs.
5. Add README gallery and capability table with evidence paths, route status, and limitations. Document using the rendered MP4 as a hashed asset in videogen without implying edited-timeline support.

## Constitution check

- Canonical implementations and adapted guidance remain in the existing video animation skill.
- Rendered evidence is required before claiming capability.
- The builder and output contract use project-relative paths and no channel-specific assets.
- Tests and exact media review verify real output. Production render approval remains separate.

## Verification

Run catalog and renderer unit tests, three Blender 5.3 previews and full renders, FFprobe frame and size checks, visual review of three motion sequences, GIF decode checks, `npm run check:docs`, and `npm run check:capabilities`. Review staged files before commit and verify push to `main`.
