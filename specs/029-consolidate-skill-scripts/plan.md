# Implementation Plan: Consolidate skill scripts

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Technical context and design

The former top-level script files are Python `runpy` or JavaScript re-export shims. Their nested targets already exist. Remove those shims and the duplicate AutoCut agent file; retain the nested implementations. Replace active old paths with canonical paths, update the Hairline upstream lock, and assert that retired folders do not reappear in the source or an install. Bump the package version for a fresh versioned install.

## Constitution check

- One canonical implementation: nested skills own executable helpers.
- Portable interfaces: paths remain repository-relative or skill-relative.
- Real validation: command smoke tests, discovery, docs, focused suites and install checks.
- Reproducible release: new version copies only canonical tree and preserves older managed-link cleanup.

## Verification

Run relevant Python and Node tests, `npm run check:docs`, and `npm run build`. Inspect staged diff and installed release contents before reporting completion.
