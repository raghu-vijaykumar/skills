# Feature Specification: Consolidate skill scripts

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: Ready for implementation

## User stories

### P1: Run a skill from its owning folder

Every operational script is in its canonical nested skill. Retired top-level skill folders contain no forwarding scripts or duplicate agent configuration.

**Acceptance**: All retired script folders are absent; every prior wrapper target exists in its nested skill; canonical commands still run.

### P2: Follow an accurate command

Current skill documentation and code point directly to nested scripts. The upstream style lock points to the retained upstream files.

**Acceptance**: Active references to retired script paths are gone; documentation and discovery checks pass.

### P3: Install a clean release

The next version installs canonical scripts without retired wrapper folders, while retaining managed-link retirement for older installations.

**Acceptance**: Installer tests and a local install verify the retired folders are absent and the canonical skill scripts exist.

## Requirements

- Keep canonical script behavior, CLI contracts, and unrelated files unchanged.
- Remove only verified forwarding wrappers and duplicate agent configuration.
- Remove the now-empty retired folders and update their active callers.
- Validate, review the staged diff, commit, push, and install on `main`.
