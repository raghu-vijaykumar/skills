# Reflection decision example

The [positive detector sheet](detected-reflection.jpg) uses a 1.25-second,
640 × 360, 8 fps synthetic reflection over a shot from the published Out of
Office Mode Tomato Bath video near 4:05. A mirrored shot from the published
Dubai Fountain video near 1:35 was blended at 22% opacity. The detector returned
`UNSUPPORTED` for the strong candidate and the red mask also covers part of the
hand, a visible false positive. This demonstrates why the mask cannot be treated
as a separated reflection layer.

The [bounded preview](bounded-preview.jpg) is a frame from `preview.py`'s
before/after comparison for `scene-001`. It returned `review_required`; the
reflection remains visible. The [AI review frame](ai-review.jpg) is from `ai.py`
using the optional DSRNet checkpoint at `--strength 0.5`. Its delivered-output
report returned `REVIEW`: relative candidate reduction 8.9%, mean-luma change
0.027, sharpness ratio 0.898, and all safety checks passed. The visual change is
subtle. The checkpoint SHA-256 was
`337e23a63fd93fc154330a6bbe21894ebd030fe9b8fa68ea7a6c8173e90f83aa`;
the checkpoint is not committed.

The older [negative detector sheet](contact-sheet.jpg) is also an actual output
from a synthetic clip. Both scenes returned `SKIP` because no candidate rose
above threshold. That is a negative result, not a demonstration of removal.

```text
scene-001: SKIP (candidate 0.000, glare 0.000, veil 0.000)
scene-002: SKIP (candidate 0.000, glare 0.000, veil 0.000)
decision: leave the source unchanged
```

`fix` renders only approved minor glare/veil scenes. `preview` renders a bounded
comparison for REVIEW/UNSUPPORTED scenes. `benchmark` evaluates an external licensed
backend. `ai` runs the optional DSRNet review pass and always returns review_required.
`generative-removal` is unsupported; no generative backend is bundled.
