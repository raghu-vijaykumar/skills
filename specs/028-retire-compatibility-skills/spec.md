# Feature Specification: Retire compatibility skill entrypoints

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: Ready for implementation

## User journeys

### P1: Discover only the skills that do work

Content Studio exposes the canonical root, Social and Video skills without the old top-level compatibility-only names. Nested operation skills remain independently callable.

**Acceptance**: All 14 compatibility entrypoints are absent from recursive discovery; their canonical destinations remain present.

### P2: Upgrade an existing installation

A user installing the next bundle version loses managed links for retired names, without deleting user-owned folders or operational scripts.

**Acceptance**: The installer removes managed retired junctions from supported skill directories and leaves external or unmanaged targets alone. Runtime files colocated with old wrappers remain in the bundle.

### P3: Follow current documentation

Current skill instructions, examples and documentation point to canonical skill names. Historical specs and non-skill script paths may retain their original labels for provenance and compatibility.

**Acceptance**: Local links validate, installation discovers the expected canonical skills, and no active skill instructs invoking a removed entrypoint.

## Requirements

- Preserve existing CLI commands, source scripts, tests, references, draft formats and publication gates.
- Remove only compatibility-only `SKILL.md` files, plus empty folders where applicable.
- Update installer retirement list, tests, docs and package version.
- Make canonical-only skill entrypoints the default rule in repository `AGENTS.md`.
- Commit and push the reviewed feature on `main`, then install it locally.
