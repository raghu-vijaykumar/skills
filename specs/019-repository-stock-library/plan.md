# Implementation Plan: Repository stock library

**Spec**: [spec.md](spec.md) | **Date**: 2026-11-11

## Approach

Use `content-studio/skills/content-studio-video/stock-library/assets/` as the canonical catalogue root. Copy the old `catalogue.json`, generated `README.md`, and seven media files while checking SHA-256. Move the old `.content-studio` evidence to the task's local visualization folder. Add a narrow Git ignore for unknown-rights WAVs. Keep the existing Git LFS media rules for the three owned CTA MOVs.

Update `library.py` to permit only this canonical repository library within the repo. Update stock and Reel skill instructions, README examples, and the managed installer filter so the local WAVs and review records never enter a release. Regenerate the asset README from the catalogue, run focused tests, documentation and capability checks, and confirm source and installed paths. Stage only owned media, catalogue, code, tests, and docs; inspect the staged diff and LFS pointer list before committing and pushing. Verify the remote branch. After that, verify copied file hashes again and remove only the old stock-library folder.

## Gates

The repository is public. The user chose to keep the four unknown-rights Reel WAVs local and ignored by Git. No permission to redistribute them is inferred. The production source and review artifacts remain outside Git. This is a storage migration and does not edit the sound or video content.
