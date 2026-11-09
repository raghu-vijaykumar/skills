# Implementation plan: Reusable 4K CTA and HLG composition

**Date:** 2026-11-09
**Spec:** [spec.md](spec.md)

## Summary

Extend the existing motion-graphics skill with a transparent stock-clip generator, an optional ingredient heading, and a narrow HLG composer that validates a versioned manifest. Use the approved Content Studio precheck plan for this draft; obtain separate approval of the resolved manifest after bounded previews.

## Technical context

- Python 3, Pillow, and FFmpeg are available. Pillow draws original RGBA vector-like frames, streamed into FFmpeg ProRes 4444 with alpha.
- The existing `overlay.py` generates ASS from cue JSON, preserving all other veg palav events.
- `hdr_compose.py` converts the SDR intro to BT.2020/HLG, applies ASS and the CTA to the untouched 10-bit HLG clean source, concatenates picture and audio, and encodes one HEVC Main10 output.
- A 2-second 4K HLG NVENC pilot took 6.25 seconds on the current RTX 2070 Super. Sustained export may differ.
- The standard delivery timeline is SDR-only. This narrow manifest supports only the explicitly named operations and rejects other keys and mismatches.

## Constitution check

- One canonical implementation lives in `content-studio-video/edit/motion-graphics`; generated media stays in the content project.
- Paths, dimensions, brand colors, and placement are inputs. No machine-specific paths are embedded in runtime code.
- New CLI contracts get focused tests and skill documentation. Actual 4K previews and output frames are inspected.
- No release tag is created as part of this draft update.

## Interface and data

- `cta_stock.py render --output ... --width ... --height ... --fps ... --duration ... --position ...` creates a transparent animation and rejects overwrite.
- `overlay.py` accepts optional `heading` on an `ingredient_list` event.
- The manifest records `schema_version`, `revision`, source/intro/sidecar/stock paths and SHA-256 hashes, `intro_seconds`, `stock_start`, `stock_duration`, frame and color settings, and audio policy. `hdr_compose.py` validates it, produces bounded previews, reports a fingerprint, requires a matching human approval for final render, and verifies delivered media.

## Review path

Inspect the generated CTA's transparent and composited frames at entrance, all button changes, and exit. Review intro, ingredient, and closing previews at 4K. Obtain approval of the exact manifest fingerprint, render once, inspect source-equivalent and affected ranges, check audio sync and color metadata, then record final-review evidence.
