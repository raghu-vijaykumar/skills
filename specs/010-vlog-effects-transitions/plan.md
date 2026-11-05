# Implementation plan: Vlog effects and transitions

**Date:** 2026-11-04  
**Spec:** [spec.md](spec.md)

## Summary

Extend the existing motion-graphics ASS renderer with generic, timed graphic effects. Add a small Remotion component module to the existing videogen runtime for the same effect names and for true two-scene transitions. Keep finished-video handling in the current validated sidecar/preview path.

## Technical context

- Python 3.13 generates ASS vector graphics; `overlay.py` already probes sources and guards Dolby Vision preview re-encodes.
- TypeScript 7, React 19, and pinned Remotion 4.0.518 build the reusable composition components.
- The package's existing `./runtime/*` export exposes the compiled module. No extra dependency or new media asset is needed.
- Tests use Python unittest, Node package tests, `npm run build`, and short visual renders.

## Constitution check

- One implementation per target: existing ASS script for finished files, runtime component for Remotion. Shared preset names and defaults are documented as the interface.
- Project paths, colors, and dimensions stay inputs; no channel branding in code.
- Public cue/runtime contracts receive tests and docs. Visual output is reviewed from actual renders.
- No release tag is planned without a clean consumer install.

## Source changes

- `content-studio/skills/content-studio-motion-graphics/scripts/overlay.py`: effect validation and ASS shapes.
- `content-studio/skills/content-studio-videogen/runtime/vlogEffects.tsx`: effect and two-scene transition components.
- Existing skill docs, video workflow reference, and root README: usage and color contract.
- Existing test folders: cue and runtime behavior.

## Review path

Render a short effects demo over an 11-second source range and a small Remotion composition, inspect entry/peak/exit frames, then run the targeted and repository checks.
