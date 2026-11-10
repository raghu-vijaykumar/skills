# Blur review capability matrix

Inspect blur candidates and apply only human-approved camera-clip cuts. The
synthetic example below shows the real scanner's flagged frame and unapproved
CSV row; it does not demonstrate an authorized cut.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Examples are illustrative evidence, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `approved-cuts` | Supported | review.csv with human-approved remove=yes spans → cut clip | No | [Animated clear/blur range comparison](previews/blur-candidate.gif) and [actual scanner CSV](previews/scan-review.csv) | Human approval mandatory; the gallery row has no `remove=yes` and no cut output. Low sharpness is not permission to delete. |

## Evidence note

The [gallery builder](previews/build_gallery.py) makes a three-second FFmpeg
test pattern with a deliberately blurred 0.75-second span. The existing
`preprocess.write_review` scanner found one candidate at 0.979–1.771 s and
left `remove` blank. The GIF compares a clear 0.75-second source range beside
the flagged 0.75-second range. Run it from the repository root with:

```powershell
python content-studio/skills/content-studio-video/source/blur-review/previews/build_gallery.py
```

This only demonstrates diagnosis. A production cut needs an approved precheck,
an editor's explicit `remove=yes` decision, and verification of the cut output.
The [illustrative review columns](previews/example-review.csv) are a schema
example, not a record of human approval.
