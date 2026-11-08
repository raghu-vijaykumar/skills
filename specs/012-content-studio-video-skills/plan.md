# Implementation Plan: Content Studio video skill migration

**Branch**: `raghu/content-studio-video-skills` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary

Move the maintained video code under `content-studio/skills/content-studio-video/`, expose each usable category and operation as a directly installable skill, keep old public entrypoints as thin compatibility layers, and align the camera workflow, prompts, and repository guidance.

## Technical Context

- **Languages**: Python 3, Node 22, TypeScript/React for Remotion.
- **Dependencies**: Existing FFmpeg, Remotion, Python media libraries, and optional local models. No new mandatory remote service.
- **Storage**: Media and precheck evidence remain in the content draft; repository contains only skills, scripts, tests, and docs.
- **Tests**: Existing Python unittest and Node test suites, docs check, clean-install smoke tests, and one raw-folder/manual-render routing test.
- **Target**: Windows-first local skills, portable npm package and installed skills.
- **Compatibility**: Keep `content-studio`, `videogen`, npm runtime exports, and old skill names working.

## Constitution Check

- One canonical implementation: move maintained code, use compatibility dispatchers only at old paths.
- Teaching and rendered evidence: no media enhancement is assumed successful from a code test; plan reviews final output.
- Portable interfaces: no channel-specific paths or mandatory branding in migrated skills.
- Real validation: existing gates and tests remain active.
- Reproducible releases: no generated media or credentials; test a clean tagged-style install before release.

## Structure Decision

Keep lifecycle `content-studio/` and precheck `content-studio-workflow/` at the bundle skill root. Add `content-studio-video/` with planning, source, edit, animation, audio, review, memory, memes, and delivery category skills. Move existing implementation folders into their closest owner. Large existing shared engines may temporarily remain within `edit/clip-edit/` or `animation/videogen/`, while operation skills expose distinct supported method scripts and list unsupported future methods without executable placeholders. Keep old skill names as short forwarding entrypoints. Update npm paths and installer recursion from one source mapping.

## Phase 0 Research

See [research.md](research.md). The installer currently assumes 18 direct children; npm exports and build paths point to the old videogen folder; several Python and Node modules compute paths from their former depth. These are the compatibility seams to update and test.

## Phase 1 Contracts

- [Skill contract](contracts/skill-discovery.md): every nested SKILL.md has a unique frontmatter name and a resolvable local method entrypoint.
- [Method contract](contracts/methods.md): one implemented method per script entrypoint, explicit support status, plan binding, and review evidence.
- [Data model](data-model.md): skill manifest and method descriptors.
- [Quickstart](quickstart.md): install, route, compatibility, and regression checks.

## Implementation sequence

1. Update recursive discovery, validation, and installer tests before moving implementation.
2. Move existing skill sources and fix relative imports, path resolution, npm exports/build, CLI wrappers, and test paths.
3. Add category and leaf operation skills with method registries; split current multi-method entrypoints where a working method exists.
4. Change default camera workflow to preprocessing handoff, opt-in AutoCut, later voice, full-edit upscale, then overlays.
5. Update four prompts, both READMEs, AGENTS.md, proposal status, and all changed skill docs.
6. Run focused and full tests, docs and installer checks, review staged diff, commit and push.

## Risks

Relative-path drift can break installed copies and project imports. Add explicit path-resolution tests and a temp-target install. A direct folder move can expose unimplemented methods; never advertise a proposed script as executable until it has a backend. HDR/DV and audio changes need media evidence before any production claim, but no content draft is changed in this migration.
