# Portrait reframe workflow

Use this when the source footage is landscape but the deliverable is a 9:16
Short, Reel, or vertical cut.

## Pipeline

```text
landscape clip
  → sample frames in the selected range
  → subject box from AI/vision annotations   (best)
  → edge/contrast saliency                   (fallback)
  → center crop                              (last resort)
  → stable 9:16 crop window
  → preview with crop rectangle
  → timeline render at 1080x1920
```

## AutoCut command

```powershell
python <autocut>/scripts/autocut.py `
  --folder <draft>\analysis\autocut-input `
  --duration 60s `
  --size 1080x1920 `
  --orientation portrait `
  --include-mismatched `
  --fit reframe `
  --reframe-mode auto `
  --subjects <draft>\analysis\subjects.json `
  --detect-scenes
```

- `--size 1080x1920` makes the master portrait.
- `--orientation portrait` sets the intended target.
- `--include-mismatched` keeps landscape sources.
- `--fit reframe` crops each selected segment to 9:16.
- `--reframe-mode auto` uses AI boxes when available, then saliency, then center.
- `--subjects` is optional; without it, saliency and center drive the crop.

## Subject box input

Coordinates are normalized 0–1 relative to the source frame:

```json
{
  "subjects": [
    {
      "source": "IMG_2204.MOV.mp4",
      "start": 12.0,
      "end": 28.0,
      "box": {"x": 0.42, "y": 0.18, "w": 0.18, "h": 0.44},
      "confidence": 0.94,
      "label": "person"
    }
  ]
}
```

Use a vision model or manual review to produce these boxes. Prefer the primary
subject; for groups, use the highest-confidence or largest relevant box. The
analyzer selects the highest-confidence box active at each sampled time.

## Output

AutoCut writes:

```text
rough-cut/
  edit-decisions.json          # reframe records and preview paths
  reframe-preview/
    shot-0000/reframe-review.html
    shot-0000/preview/marked-00.jpg
    shot-0000/preview/cropped-00.jpg
  timeline.json                # each clip carries a reframe record
  rough-cut.mp4                # 1080x1920
```

A reframe record:

```json
{
  "source": "IMG_2204.MOV.mp4",
  "source_width": 1920,
  "source_height": 1080,
  "target_width": 1080,
  "target_height": 1920,
  "mode": "subjects",
  "crop": {"x": 0.34, "y": 0.0, "w": 0.3164, "h": 1.0},
  "confidence": 0.94
}
```

The renderer applies:

```text
crop=<w>:<h>:<x>:<y>,scale=1080:1920
```

## Review

Open each `reframe-review.html` and check:

- the red crop rectangle contains the subject
- the cropped image keeps the face/product/action readable
- the crop does not cut off important context
- confidence is reasonable; low confidence deserves manual review

If a long segment has a moving subject, split it into shorter source ranges and
re-run, or provide per-range subject boxes. The current implementation uses one
stable crop per selected segment; dynamic crop tracking is not implemented yet.

## Standalone analysis

```powershell
python <autocut>/scripts/reframe.py `
  --input <clip> --start 12 --end 28 `
  --size 1080x1920 --mode auto `
  --subjects <draft>\analysis\subjects.json `
  --output <draft>\analysis\reframe
```

Modes:

| Mode | Behavior |
|---|---|
| `auto` | AI boxes first, saliency fallback, center last |
| `subjects` | Require subject boxes; error when none cover the range |
| `saliency` | Edge/contrast heuristic only |
| `center` | Center crop only |

## Limitations

- One stable crop per selected segment.
- Saliency is not semantic understanding; it prefers edge-dense, centered regions.
- Faces are not detected without AI boxes.
- Portrait output is SDR H.264/AAC; Dolby Vision is not preserved.
- The preview is a proposal; a human must approve the framing before publishing.
