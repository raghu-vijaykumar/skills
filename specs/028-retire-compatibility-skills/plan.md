# Implementation Plan: Retire compatibility skill entrypoints

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Delete the 14 top-level routing-only skill entrypoints, retain colocated working files, and make the versioned installer unlink managed old skill links. Replace active references to removed skill names with canonical Social or Video names. Keep old command paths that still point to real scripts.

## Constitution check

- One canonical implementation: nested skills and existing scripts remain the owners.
- Real validation: discovery, link checks and installation tests verify the removal.
- Reproducible release: bump the version to create a clean install tree and preserve unmanaged user files.

## Verification

Run the skill-discovery and installer tests outside the Windows junction sandbox, `npm run check:docs`, `npm run build`, and the relevant Node suite. Inspect staged deletions and changes. The known unrelated voice-cloning capability-matrix failure remains separately reported if the full suite fails. Commit, push and install the new version locally; verify all 14 managed compatibility links are gone.
