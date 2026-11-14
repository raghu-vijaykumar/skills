# Implementation Plan: Fast pan cuts

**Branch**: `main` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

## Summary

Create a nested `edit/fastpan-cuts` skill with a deterministic Python CLI for source-linked motion diagnosis, bounded cut previews, and native timeline changes. Reuse the timeline's existing picture-span renderer and approval gates. No final master is encoded by the new skill.

## Technical context

- Python 3 with NumPy, FFmpeg, FFprobe, and Pillow already used by Content Studio.
- Source report and human cut decisions are JSON files under a draft's `.content-studio/analysis/fastpan-cuts/`; generated media remains local and out of Git.
- Input is one SDR CFR video. Sample at 4 fps and 320 × 180 for broad motion discovery; validate candidates against real frames before proposing source-frame cuts.
- The preview command decodes only a bounded window, trims picture and audio to matching source ranges, then encodes a small review MP4.
- Timeline handoff emits complete `picture` replacement ranges for one untouched source clip. The existing timeline still validates, fingerprints, approves, renders, and verifies the final file.

## Constitution check

- One canonical implementation: the new skill owns its CLI; the timeline remains the canonical final renderer.
- Portable interface: every path, range, and output is supplied as an argument; no Dubai-specific logic or private media enters Git.
- Real validation: synthetic pan and edit tests, capability matrix, skill discovery, documentation checks, and bounded rendered evidence.
- Reproducibility: stable source hashes and frame indices; generated previews remain outside the repository.

## Project structure

```text
content-studio/skills/content-studio-video/edit/fastpan-cuts/
  SKILL.md
  README.md                 capability matrix and synthetic evidence route
  methods.json
  scripts/fastpan.py
  tests/test_fastpan.py
  previews/                 small synthetic report, validation, and animated cut comparison
specs/020-fastpan-cuts/{spec,plan,tasks}.md
```

Update the edit router, video capability index, root README, and matrix count check. Inspect the staged diff, then commit and push only feature files.

## Review gates

`scan` and bounded previews can inform the required workflow plan. The human decides exact removal frames. Exporting timeline changes does not approve them or render a master. A changed workflow plan or timeline needs renewed human approval. The Day 5 source and its contact sheets remain outside Git.
