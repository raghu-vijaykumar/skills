---
name: content-studio-video-reflection
description: Detect reflection-affected regions in video, classify them, apply only conservative glare or veil fixes, preview bounded candidates, and run a pretrained DSRNet AI review pass that attenuates reflections without claiming reconstruction.
---

# content-studio-video-reflection

Complete the mandatory [`content-studio-workflow`](../../../content-studio-workflow/SKILL.md) precheck before editing. State the exact method script, input, output, estimate, fallback, and review criterion, then obtain approval of that plan revision. This skill is diagnosis-first: a detected candidate is not proof of a separable reflection layer.

No generative reflection-removal backend is bundled. A pretrained **DSRNet**
separation model from XReflection is available as an optional `ai` review pass.
It predicts a reflection layer and attenuates it; it does not reconstruct
occluded content, and on a strong, content-rich reflection (a shop window where
the street and the display are both clearly visible) the remaining reflection is
expected to stay visible. Results are always `review_required`, and the pass is
rejected when it shifts luma, saturation, clipping, sharpness, or temporal
stability beyond the safety gates. A successful encode is never proof that the
reflection layer was removed.

## Commands

Find candidates without changing footage:

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/detect.py `
  --file <clip> --out <draft>/.content-studio/reflection
```

Analyze every video in a folder:

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/detect.py `
  --folder <draft> --out <draft>/.content-studio/reflection
```

Render approved minor glare/veil fixes only (`FIX` scenes with an `approved` or `auto_approved` review status):

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/fix.py `
  --manifest <draft>/.content-studio/reflection/<clip>/manifests/reflection.yaml `
  --output <draft>/<clip>-reflection-fix.mp4
```

Render a short bounded comparison preview for a `REVIEW`/`UNSUPPORTED` scene. The preview is always `review_required` and never removes content-rich reflections:

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/preview.py `
  --manifest <draft>/.content-studio/reflection/<clip>/manifests/reflection.yaml `
  --output <draft>/.content-studio/reflection/<clip>/previews/scene-001-preview.mp4 `
  --scene scene-001 --seconds 3
```

Run the pretrained AI review pass. It needs PyTorch (CUDA recommended), the
DSRNet checkpoint (1.54 GB, downloaded on request), and torchvision's VGG19
weights (~0.55 GB, downloaded automatically on first use). Every frame is
decoded at native resolution, the model works on a resized copy, and only its
low-frequency correction is transferred back so native detail is preserved:

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/ai.py `
  --file <clip> `
  --output <draft>/.content-studio/reflection/<clip>/ai/<clip>-ai-review.mp4 `
  --download
```

`--max-width` (default 640) sets the model working width, `--strength`
(default 1.0) scales the correction, and `--seconds` limits a trial run. Use
`--weights` or `CONTENT_STUDIO_REFLECTION_WEIGHTS` for a checkpoint outside the
per-user cache. The pass writes `ai/work/report.json`, `report.md`, evidence
under `ai/work/keys/`, a contact sheet, and a side-by-side `compare.mp4`. It
returns `REVIEW`, `SKIP` (no measurable reduction, or the model abstained), or
`REJECTED` (a safety gate failed). It never writes `FIX` and never overwrites
the source. Record the measured runtime, peak memory, and checkpoint SHA-256 in
the plan and the evidence package.

Benchmark an external, licensed backend on the clip's evidence frames before selecting it:

```json
{
  "name": "windowseat",
  "license": "research-only",
  "checkpoint": "sha256:...",
  "command": ["python", "adapter.py", "{input}", "{output}"]
}
```

```powershell
python content-studio/skills/content-studio-video/edit/reflection/scripts/benchmark.py `
  --file <clip> --config <backend.json> --frames 3
```

The harness writes `benchmarks.json` and `benchmark.html` with runtime, candidate/glare reduction, luma change, sharpness ratio, and an accepted/rejected result. It does not install the backend or promote it to the default policy.

## Decisions

| Action | Meaning |
| --- | --- |
| `SKIP` | No candidate above the detection threshold, or the AI pass found no measurable reduction |
| `FIX` | Small persistent glare/veil; masked highlight compression only |
| `REVIEW` | Content-rich or transient candidate; inspect evidence and compare a bounded preview |
| `UNSUPPORTED` | Strong/content-rich reflection beyond the available backend's reliable range; preserve the source and review alternatives |
| `REJECTED` | The AI pass changed luma, saturation, clipping, sharpness, or temporal stability beyond its gates |

Each scene receives exactly one reflection decision. Read the manifest and evidence instead of assuming a batch result; a clip can contain both `FIX` and `UNSUPPORTED` scenes. The `ai` pass is a clip-level review artifact, not a scene decision, and never changes a scene to `FIX`.

## What the detector measures

The detector samples five frames per scene and records bright, low-saturation, low-texture regions that persist across the scene. It writes the original frame, a red candidate overlay, and a mask PNG for each sample. The candidate mask is evidence for review, not a reflection layer estimate.

## What the AI pass measures

The `ai` pass runs DSRNet on a resized copy of every frame, keeps the native frame, and adds only the low-frequency difference between the model's clean output and its own resized input. It records, for sampled frames:

- candidate, glare, and veil fractions before and after
- luma, saturation, clipping, and sharpness before and after
- mean absolute predicted reflection energy
- frame-to-frame step in the output relative to the source (temporal flicker)

It returns `REVIEW` only when the candidate fraction drops by at least 0.0015 absolute or 5% relative, the model predicted a non-trivial reflection layer, and luma change <= 0.05, saturation change <= 0.05, clipping increase <= 0.02, sharpness ratio 0.85-1.20, and flicker ratio <= 1.35. Anything else is `SKIP` or `REJECTED`. A `REVIEW` result still requires a human comparison against the source; partial attenuation is not reconstruction.

Read [the reflection policy](references/reflection-policy.md) for thresholds, false-positive cases, the verification gate, and the backend selection criteria.

## Output package

```text
.content-studio/reflection/<clip>/
  analysis/report.json
  analysis/evidence/*.jpg
  analysis/overlays/*.jpg
  masks/*.png
  manifests/reflection.yaml
  reports/reflection.html
  previews/contact-sheet.jpg
  previews/*-compare.mp4
  rendered/
  benchmarks/
  ai/work/report.json
  ai/work/report.md
  ai/work/keys/*.png
  ai/work/compare.mp4
  ai/<clip>-ai-review.mp4
```

Analysis is cached by source SHA-256 and `analysis_version`; a changed source forces a fresh analysis. The renderer refuses a source whose hash changed since detection. Approved `FIX` renders are sampled at 20%, 50%, and 80% of each corrected scene and rejected when the candidate fraction does not improve or luma, saturation, or clipping leave their safety limits. The `ai` pass re-checks its gates on sampled frames of its own exact output and records every failure in `ai/work/report.json`. HDR/HLG sources are refused until an explicit tone-map decision is recorded. Originals are never overwritten.
