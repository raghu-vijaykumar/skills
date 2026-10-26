# Implementation Plan: videogen extraction

**Branch**: `raghu/videogen` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

Package the generic Remotion runtime and tools as `videogen/` in this skills repository. Keep Revise Labs as a tagged-package consumer and content owner.

## Technical context

- Node 22, TypeScript/React, Remotion 4.0.518, npm, ffmpeg/ffprobe, optional Python edge-tts.
- Windows PowerShell is a required development and consumer platform.
- Git-tag installation reads the root `package.json`; package files include only `videogen/`.

## Interfaces

- `videogen.config.ts`: `defineProject({entryPoint, videosDir, contentDir, theme, styles, checks?, outro?})`.
- `video.yaml`: `video.compositionId` identifies the primary Remotion composition.
- `videogen` CLI: `init`, `new video`, `new content`, `narration`, `check`, `render`, `content check`, `content render`, `sync-skill`.
- Runtime exports: animation, reusable components, themes, styles, and registration helpers.

## Migration

Start with a neutral fixture and Revise Labs pilot for semantic video, video/post package, and fixed-duration landscape intro. Migrate all implemented videos in batches, update old timing contracts, and verify frames. Remove the two abandoned drafts and reconcile documents.

## Gates

Unit and integration checks, expected-failure fixtures, clean Git-tag install, package contents, Codex/OpenCode skill discovery, Studio frame review, `check:docs`, and staged diff review. Full-length delivery is separately requested.
