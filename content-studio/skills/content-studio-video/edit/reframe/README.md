# Reframe capability matrix

Create reviewed portrait crops from finished or approved video ranges. These
previews animate actual 9:16 crop proposals across 1.5-second excerpts of two already
published Out of Office Mode videos. The moving marked source is on the left and the
proposed portrait crop is on the right; these methods write review images and JSON, not a
delivered portrait video. Both original videos are untouched.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Examples are illustrative evidence, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `subjects` | Supported | Landscape video + subject boxes → stable crop preview + reframe.json | Specialist only | [Animated pot box and crop](previews/subjects-crop.gif) / [box JSON](previews/example-subjects.json) | The pot box was supplied by the operator; one stable crop per range. |
| `saliency` | Supported | Landscape video → crop preview + reframe.json | Specialist only | [Animated fountain saliency crop](previews/saliency-crop.gif) | Heuristic selected the high-detail building and cut off most of the fountain: a review failure, not object understanding. |
| `center` | Supported | Landscape video → crop preview + reframe.json | Specialist only | [Animated center crop](previews/center-crop.gif) | Deliberate center crop; may cut the subject. |

## Review the crop proposals

![Operator-supplied pot box and proposed crop](previews/subjects-crop.gif)

![Saliency proposal on the fountain shot](previews/saliency-crop.gif)

![Deliberate center crop of the cooking shot](previews/center-crop.gif)

`subjects.py` and `center.py` used the published Tomato Bath shot near 4:05;
`saliency.py` used the published Dubai Fountain shot near 1:35. Each was sampled
at 640 × 360, 8 fps for 1.5 seconds. The subject box input uses the actual
accepted schema in [example-subjects.json](previews/example-subjects.json).
To rebuild the GIFs, run the three method scripts with `--size 180x320`, then
pass their output directories and the two bounded source clips to
`scripts/build_gallery.py` using `--source-cooking` and `--source-fountain`.

## Evidence note

The GIFs use already published footage, not private draft media or full masters.
The method's `reframe.json` supplies the red rectangle and stable crop geometry;
the gallery script applies it at each source frame for animated review. It does
not create a delivered portrait video.
