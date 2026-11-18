# Implementation Plan: Content Studio Social skill tree

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Create a short Social router and seven nested leaves: YouTube publish/analytics, LinkedIn author/publish/analytics, and Instagram publish/analytics. Move the canonical LinkedIn author guidance beneath Social, with its old top-level name retained as a compatibility entrypoint. Link publishing leaves to the existing YouTube/Instagram video publisher and LinkedIn CLI rather than copying code. Route YouTube analytics to the existing `content.py insights` and `analytics` commands. Describe export-based LinkedIn and Instagram analytics without a new API client.

## Technical context

Markdown skills with YAML frontmatter are recursively discovered by `skill-discovery.mjs` and installed as versioned junctions. Existing implementation is in Node ESM and Python. Tests use Node's test runner and `check:docs` validates local links and unique names.

## Constitution check

- One canonical implementation: publisher and collector scripts stay at their existing owners.
- Real validation: no analytics or publication capability is claimed beyond repository behavior.
- Portable interfaces: routing avoids hard-coded channel identities.
- Reproducible release: bump package version, validate recursive discovery and a local installation; keep credentials and analytics out of Git.

## Structure

```text
content-studio/skills/content-studio-social/
  SKILL.md
  youtube/publish/SKILL.md
  youtube/analytics/SKILL.md
  linkedin/author/SKILL.md
  linkedin/author/references/workflow.md
  linkedin/publish/SKILL.md
  linkedin/analytics/SKILL.md
  instagram/publish/SKILL.md
  instagram/analytics/SKILL.md
```

The existing `content-studio-linkedin` path becomes a compatibility route to Social LinkedIn Author. Content Studio's top-level router and README point to Social. Video ideation refers to Social YouTube Analytics for owned measurement while retaining its planning implementation.

## Verification

Test exact discovery names and legacy route, validate docs, run the relevant Node tests and build, inspect the staged diff, commit and push `main`, then install the versioned skill bundle locally. Report the existing unrelated full-suite capability-matrix failure if it persists.
