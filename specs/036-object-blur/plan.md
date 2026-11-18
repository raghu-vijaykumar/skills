# Implementation Plan: Named object blur

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Technical design

Add `edit/object-blur` as an independently callable leaf. Its `analyze` command reads exactly the scale/pad/fps frame sequence of one approved uncut SDR delivery timeline. Grounding DINO Tiny detects the phrase on every frame; SAM 2.1 Tiny segments each box in a separate pass to limit GPU memory. Both revisions are pinned. A normalized optional click selects one instance; corrections replace boxes or adjust polygons. The output is a lossless gray FFV1 mask and source-linked JSON evidence under the draft.

The `changes` command emits a pending timeline `object-blur` operation. The timeline validates source, mask, analysis, frame count, dimensions, duration, and human coverage review. Its renderer splits the resolved video, strongly blurs one branch, uses the gray mask as alpha, and encodes the composite once. Capability and asset hashes enter the existing approval fingerprint.

The first route is deliberately limited to a full finished SDR render in one uncut picture entry. Cuts baked into the finished render are analyzed frame by frame. Other picture operations and timeline remapping are rejected. Audio cues remain supported. A bounded model pilot supplies the per-frame time estimate in a production preflight; model weights and draft media stay outside Git.

## Constitution check

One canonical leaf owns detection and mask creation; the timeline owns final export. Inputs are project paths, a target phrase and optional normalized coordinates. Tests cover failure gates and exact rendered evidence, not just JSON shape. No production media or credentials enter the package.
