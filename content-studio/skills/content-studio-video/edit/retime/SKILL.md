---
name: content-studio-video-retime
description: Propose and review finite speed, freeze, reverse, and loop spans on an approved delivery timeline.
---

# Retime on the delivery timeline

Complete the mandatory `content-studio-workflow` precheck and obtain approval of
the current plan before editing. Use this skill only for an explicit request to
change a supplied SDR H.264 edit. The raw-camera route still stops for the
user's manual edit. Name the chosen [method](methods.json), source span, audio
treatment, exact command, time estimate, output revision, and fallback in the
precheck. Read the [method limits and review loop](references/retime.md).

`scripts/retime.py propose` writes a reviewable `changes.json` and report. The
canonical timeline `revise` command applies that change to a new immutable
revision after current preflight approval. `scripts/retime.py preview` renders a
bounded range of that revision. Human review of motion, sound, duration, and
later cues precedes separate timeline approval and the one final export. Verify
the exact master before package approval; a preview is never final proof.
