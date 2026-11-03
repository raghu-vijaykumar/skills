# Diagnosis-first video enhancement

Use this workflow to inspect footage for real quality defects before changing a
single pixel. It is deliberately conservative:

- clean footage is skipped
- color corrections are temporal and quality-gated
- strong reflections are never auto-removed
- every decision is reproducible from a manifest

## Commands

Analyze a folder without changing footage:

```powershell
content-studio enhance analyze --folder <draft>
```

Analyze one clip and write the review package under `.content-studio/enhancement`:

```powershell
content-studio enhance analyze --file <clip>
```

Create the same analysis plus auto-approval for scenes where every issue is
`FIX` or `SKIP`:

```powershell
content-studio enhance analyze --file <clip> --auto-fix
```

Analyze sources referenced by an editable timeline:

```powershell
content-studio enhance analyze --timeline <draft>/.content-studio/rough-cut/timeline.json --selected-clips
```

The timeline source ranges are used to choose which files to inspect; corrections
are still planned at the source-clip scene level.

Render approved corrections:

```powershell
content-studio enhance render `
  --manifest <draft>/.content-studio/enhancement/<clip>/manifests/enhancement.yaml `
  --output <draft>/<name>-enhanced.mp4
```

The Python entry point is also available directly:

```powershell
python <bundle>/skills/content-studio-videoedit/scripts/content.py enhance analyze --folder <draft>
```

## Reflection backend benchmarks

No reflection model is bundled. Evaluate a licensed backend on the clip's
reflection evidence frames before selecting it:

```json
{
  "name": "xreflection",
  "license": "research-only",
  "checkpoint": "sha256:...",
  "command": ["python", "adapter.py", "{input}", "{output}"]
}
```

```powershell
content-studio enhance benchmark --file <clip> --config <backend.json> --frames 3
```

The harness writes `benchmark.html` and `benchmarks.json` with runtime, glare
reduction, luma change, sharpness ratio, and an accepted/rejected result. It
does not install the backend or change the default reflection policy.

Approved renders also write side-by-side before/after JPEGs and short playable
MP4 previews under `previews/before-after/`.

## Decisions

Each detected issue receives one action independently:

| Action | Meaning |
| --- | --- |
| `SKIP` | No issue, or no meaningful improvement is expected |
| `FIX` | A conservative technical correction is planned |
| `REVIEW` | Evidence is uncertain or the correction needs human approval |
| `UNSUPPORTED` | The required backend is unavailable or unlicensed |

A scene's decision is the strongest action across its issues:
`FIX` > `REVIEW` > `UNSUPPORTED` > `SKIP`.

## Analysis

The analyzer records:

- codec, frame rate, resolution, rotation, HDR/SDR transfer, audio presence
- FFmpeg scene cuts, split into analysis chunks when a scene is long
- three sampled frames per scene with reusable evidence JPEGs
- luma mean/std/percentiles, clipping, saturation, channel means, glare
  fraction, and a simple sharpness measure

Detected issues currently include:

- underexposure
- highlight clipping / overexposure
- white-balance cast
- low contrast
- low or high saturation
- glare / strong reflection

## Color correction

Only color issues with `FIX` are rendered. Corrections are applied with FFmpeg
timeline `enable` expressions, so unaffected scenes keep their original pixels.
Supported technical corrections:

- exposure brightness
- contrast
- saturation
- white-balance channel gains

Creative grading is not part of this analyzer. Add it as an explicit,
separate step.

## Reflections and glare

Reflection separation is **not** applied automatically. The current cascade is:

| Situation | Action |
| --- | --- |
| No glare | `SKIP` |
| Minor glare | `REVIEW` |
| Strong reflection / large glare area | `UNSUPPORTED` |
| Licensed backend installed and benchmarked | explicit integration required |

Do not treat inpainting as faithful reconstruction. XReflection, WindowSeat,
GenSIRR, PRISM, and ProPainter must be evaluated for accuracy, temporal
stability, license, runtime, and GPU memory before one is selected as a default.

## Output package

```text
.content-studio/enhancement/<clip>/
  analysis/report.json
  analysis/evidence/*.jpg
  manifests/enhancement.yaml
  reports/quality.html
  masks/
  previews/
```

The manifest records source hash, analysis version, model/backend provenance,
parameters, evidence frames, review status, and validation results.

## Safety and resume

- Analysis is cached by source SHA-256 and `analysis_version`.
- A changed source forces a fresh analysis.
- Rendering refuses a source whose hash changed since analysis.
- A correction that shifts luma, saturation, or clipping beyond the validation
  limits is rejected and the output is deleted.
- Originals are never overwritten. `--output` must differ from the source.

## Current limitations

- OpenCV and PySceneDetect are not required; scene detection and metrics use
  FFmpeg, NumPy, and Pillow.
- The color model is heuristic, not a calibrated colorimeter.
- Reflection detection is glare-based and conservative; it does not distinguish
  a bright sky from a glass reflection reliably.
- No reflection-removal or inpainting backend is bundled.
- The renderer applies approved color corrections only. Reflection masks and
  generative reconstruction remain future work.
- Only the first clip in a manifest is rendered; folder-level batch rendering
  should be driven from the folder report.
