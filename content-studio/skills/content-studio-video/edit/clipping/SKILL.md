---
name: content-studio-video-clipping
description: Select a hero-led passage from a finished long-form video and deliver a reviewed portrait Reel or Short.
---

# Hero-led long-form clipping

Use this leaf when the editor wants one particular long-form moment, including its visible hero and action, made into a portrait short. A simple requested trim belongs to [clip edit](../clip-edit/SKILL.md); a crop-only request belongs to [reframe](../reframe/SKILL.md). This skill owns the source-linked moment selection and its handoff into the approved delivery timeline. Do not invoke AutoCut unless separately requested.

`scripts/clipping.py inspect` creates timestamped contact sheets and an editable selection record. It may run before preflight as read-only diagnosis. A rough source range is optional; with no range, the editor searches the contact sheets and fills the chosen range. Sampled frames cannot prove that a hero is absent elsewhere, or establish a complete action or spoken line. Inspect the candidate's original picture and audio, then choose boundaries that carry the opening, action, and ending.

`propose-crop` calls the existing `subjects`, `saliency`, or `center` reframe script for one bounded interval. Prefer supplied hero boxes. For multiple heroes, supply a group box to guide the one crop and separately labelled boxes for each hero to audit individual coverage. Saliency and center are explicit review alternatives, not hero detection. Each proposal writes a new selection revision, original-versus-crop images, a hashed framing report, and portrait guide frames. The report measures the fraction of source context lost, supplied hero-box coverage, destination safe-area coverage, and hero center movement. No boxes means hero coverage is `UNSUPPORTED`; sampled boxes can still miss an action. A moving hero may need adjacent, stable crop intervals. The selection records destination-width crop-centre jumps at every adjacent boundary and requires a human note for each before timeline handoff. The tool never silently changes method or approves a crop. The editor records their range and framing decision in the selection JSON.

Before `emit-changes` or any production edit, run the mandatory [Content Studio precheck](../../../content-studio-workflow/SKILL.md) against the actual draft. Name `reviewed-hero-range`, the reframe method, the exact script arguments, output, benchmark-based estimate, fallback, and review criteria. Obtain explicit human approval of that plan revision and begin its checklist. The current route requires an SDR source and a clean portrait timeline; HDR/Dolby Vision picture processing and smooth crop tracking are unsupported.

`emit-changes` validates the reviewed selection, source and crop evidence hashes, and the approved preflight timeline. It writes pending picture and crop arrays. Revise and preview the [delivery timeline](../../timeline/SKILL.md), then obtain separate human approval of the exact timeline revision before rendering. Verify the delivered master with [final-render review](../../review/final-render/SKILL.md), including phone-size hero coverage, source range, sound boundaries, and audio sync. Complete the preflight checklist. Publication needs its own explicit request.

Read the [command guide and capability matrix](README.md) for the selection fields, exact commands, review steps, and current limits.
