# Reflection diagnosis and correction policy

Reflections are an additive, scene-dependent layer. A single frame does not
contain enough information to separate that layer faithfully: the same bright,
low-saturation region can be a reflection, a sky, a lamp, a white sign, or a
bright shop interior. This skill therefore separates **evidence** from
**correction**.

## Candidate evidence

Five frames per scene are sampled at 10%, 30%, 50%, 70%, and 90% of the scene.
For each frame:

- `glare`: luma >= 0.90, saturation <= 0.18, gradient <= 0.12
- `veil`: luma 0.58–0.96, saturation <= 0.14, gradient <= 0.035
- `candidate`: `glare | veil`, closed for pinholes, opened to remove thin
  high-detail structures, then dilated for readable evidence

The candidate mask is a review aid. It is not a reflection layer estimate and
must not be used as an inpainting mask for a strong reflection.

Scene metrics:

| Metric | Meaning |
| --- | --- |
| `candidate_mean` | Average candidate area across sampled frames |
| `candidate_peak` | Largest candidate area |
| `glare_peak` | Largest specular area |
| `persistent_fraction` | Area that stays a candidate in at least 60% of samples |
| `flicker` | Standard deviation of candidate area |

## Decision thresholds

| Condition | Action | Type |
| --- | --- | --- |
| `candidate_peak < 0.004` | `SKIP` | none |
| `persistent_fraction >= 0.06`, `candidate_peak >= 0.20`, `candidate_mean >= 0.12`, or `glare_peak >= 0.12` | `UNSUPPORTED` | strong reflection |
| `candidate_mean >= 0.05` or `candidate_peak >= 0.10` | `REVIEW` | content-rich reflection |
| `persistent_fraction >= 0.02` and `candidate_mean >= 0.004` | `FIX` | minor glare/veil |
| Otherwise | `REVIEW` | transient reflection |

These thresholds are deliberately conservative. A bright sky at the top of a
frame can cross them; treat the evidence overlay and the scene context as part
of the decision.

## Correction

`FIX` scenes use one per-scene mask and `maskedmerge` with:

```text
eq=brightness=-0.10:contrast=1.05:saturation=1.0
```

Only the masked candidate region changes. The correction is a highlight/veil
compression, not reflection separation. It must reduce the candidate fraction by
at least 0.0005 while keeping luma change <= 0.15, saturation change <= 0.30, and
clipping increase <= 0.05; otherwise the render is rejected.

`UNSUPPORTED` and `REVIEW` scenes are never auto-rendered by `fix`. `preview`
renders a short bounded comparison with a slightly stronger compression and
labels the result `review_required`. A preview is provisional evidence for the
plan, not proof of removal.

## AI review pass (DSRNet)

A pretrained DSRNet model from XReflection is wired as the optional `ai`
method. Weights are not bundled; the adapter downloads them on request and
records the SHA-256 in the report. Code provenance and the upstream license
caveat are in `backends/dsrnet/NOTICE.md`.

The pass is deliberately conservative:

```text
work_size  = multiple-of-32 size at --max-width (default 640 wide)
prediction = DSRNet(work_size) -> clean, reflection, residual
output     = native + strength * (upsample(clean) - upsample(work_size input))
```

Transferring only the low-frequency difference preserves native detail and
avoids resampling blur or tile seams. The reflection layer itself is kept as
amplified evidence (`keys/*-reflection.png`) and is never subtracted directly:
its high-frequency noise produces visible artifacts when upscaled.

`REVIEW` requires a candidate reduction of >= 0.0015 absolute or 5% relative,
a mean absolute reflection layer >= 0.002, and every safety gate passing. The
pass returns `SKIP` when the model abstains or the reduction is too small, and
`REJECTED` when a gate fails. It never returns `FIX`.

Observed limits on a 9.4 s, 1080p60 shop-window clip with a near 50/50
reflection (street reflected over a lit display):

- candidate fraction fell ~8% relative and glare fell ~6% relative;
- the street and people reflections stayed clearly visible;
- luma dropped ~0.026 and clipping fell, so the result reads as a mild veil
  attenuation, not reflection removal;
- one RTX 2070 Super (8 GB) processed about 1.1 s/frame at 640x352 fp16.

Treat that as the expected ceiling for strong reflections. Do not advertise the
pass as reconstruction, and do not use it to justify deleting the source.

## Backend selection

No generative model is bundled. The DSRNet pass is a validated baseline, not a
claim that any single-image method can recover a strong reflection. Evaluate an
alternative licensed backend on the clip's own evidence frames before selecting
it. Required evidence:

- license and checkpoint provenance
- runtime and peak GPU memory on the target machine
- candidate/glare reduction and luma change
- sharpness ratio and temporal stability
- side-by-side frames and a short playable clip
- behavior on a no-reflection control scene

XReflection/DSRNet, WindowSeat, GenSIRR, PRISM, and ProPainter are candidates for
evaluation, not defaults. Do not treat inpainting as faithful reconstruction.
Strong reflections remain `REVIEW` or `UNSUPPORTED` until the benchmark passes
and a human reviews the exact delivered output.

## Known limits

- Detection is glare/veil based; it cannot reliably distinguish a reflection
  from a bright sky, a light source, or a white sign.
- Moving camera footage mixes reflection and background motion; the detector
  does not perform motion-layer separation.
- The candidate mask over-covers shop interiors and bright displays.
- DSRNet was trained on 224 px crops and modest reflections; a near 50/50
  reflection is outside its reliable range.
- The AI pass attenuates the predicted reflection layer; it does not invent the
  occluded background, so strong reflections remain visible.
- HDR/HLG sources are refused until an explicit tone-map decision is recorded.
- The current renderer applies one masked filter per scene; per-region filters
  and generative reconstruction remain future work.
