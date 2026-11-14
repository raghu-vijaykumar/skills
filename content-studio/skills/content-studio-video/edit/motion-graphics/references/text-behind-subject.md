# Rising text behind a moving subject

Reference: [Enrique Beli's Instagram tutorial](https://www.instagram.com/reel/DfkgKmgoLVs/), reviewed 2026-11-14. The reference clip is 61.79 seconds at 1080 × 1920/30 fps. Its finished examples show a bold white place name rising from behind the landscape while the person stays in front. The phone tutorial records a static scenic shot with a person facing away, places a title on the shot, animates its vertical position with keyframes, duplicates the shot, removes the background around the foreground, and stacks that cutout above the title. The exported example repeats the reveal as the person raises their arms. The tutorial's editing app is only a visual reference; Content Studio does the effect locally with the delivery timeline and FFmpeg.

## Preset contract

`presets/text-behind-subject.json` stores the default motion and review criteria. Use the `text-behind-subject` timeline method for each chosen shot. The white portions of a grayscale matte preserve the original pixels above the title; black portions reveal the title over the base picture. The native generator uses Torchvision LRASPP's person class; it can add a static foreground polygon for a ridge or other fixed near scenery. The [Torchvision model and weights](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.segmentation.lraspp_mobilenet_v3_large.html) run locally after their first download. No third-party editor is required.

Choose a shot with space for a legible title and a clear foreground silhouette. A locked camera is best when using a static terrain polygon. The polygon must trace the visible foreground boundary and include the bottom of the frame. The person model can miss thin arms, hair, or small subjects; inspect the moving matte at the title crossing. A moving camera, complex foliage, or multiple overlapping people may need a reviewed hand-corrected matte. Never claim a faithful behind-subject effect from an unreviewed mask.

The preset supports one or multiple cues, but **each cue stays within one source shot and outside join overlaps**. Resolve the cue time on the final picture timeline. Generate the matte from the corresponding source shot, using its source time `source_in + (cue.start - picture.start)` and cue duration. If the timeline includes crops or reframes, produce a matte matching that transformed picture or revise the cue; review alignment before approval. The renderer scales the matte to the output canvas. Its current SDR timeline route does not accept HDR or Dolby Vision input.

## Fast native route

The mandatory Content Studio precheck still applies before changing a production draft. Include the source, title, matte method, exact commands, time estimate, outputs, fallback, and review criteria in the editable plan, then obtain explicit approval of that plan revision. Bounded read-only diagnosis and short comparisons can inform it.

Create one matte per title cue. The polygon file is optional and contains normalized `[x,y]` points, such as `[[0,0.55],[0.5,0.62],[1,0.5],[1,1],[0,1]]`. White terrain and person pixels must cover the title crossing; black sky stays open. Use the same frame rate as the timeline.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/subject_matte.py `
  --input <shot.mp4> --start <source-seconds> --duration <cue-seconds> `
  --fps 30 --foreground-polygon <ridge.json> --output <draft>/mattes/place-01.mp4
```

For a shot with no person, `--person off` makes a terrain-only mask. This does not silently replace a failed person segmentation. Review the generated mask video and its `.json` provenance sidecar. Keep it beside the draft; do not commit source media or masks to the skills repository.

After `timeline.py init`, create a cue sheet in the source root (paths below are relative to that root):

```json
{
  "cues": [
    {
      "id": "place-01",
      "start": 0.4,
      "end": 3.0,
      "text": "ITALY",
      "font_source": "assets/arial-bold.ttf",
      "matte_source": "mattes/place-01.mp4",
      "rise_seconds": 1.0,
      "from_y": 0.55,
      "to_y": 0.12,
      "font_height": 0.09
    }
  ]
}
```

`start` and `end` are resolved delivery-timeline seconds. `from_y`, `to_y`, and `font_height` are fractions of the final output height. The example word is illustrative; derive a real place name or other factual label from the supplied footage and reliable context. For several shots, add a cue and matte per shot with unique IDs. The helper hashes the font and matte, adds `pending_review`, and emits a revision changes file:

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/behind_subject.py `
  --timeline <draft>/.content-studio/timeline/timeline-v001.json `
  --cues <draft>/behind-subject-cues.json --out <draft>/behind-subject-changes.json
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py revise `
  --timeline <draft>/.content-studio/timeline/timeline-v001.json `
  --plan <draft>/.content-studio/preflight/plan.json `
  --changes <draft>/behind-subject-changes.json `
  --out <draft>/.content-studio/timeline/timeline-v002.json `
  --output <draft>/<id>-final.mp4
```

Validate and render a bounded preview with `timeline.py validate` and `preview`. Inspect title entrance, midpoint, settled position, moving edges, audio, and frame size. Revise font, motion, polygon, or matte if needed. After the user reviews the exact timeline and approves it, change each operation to `approved` in a new immutable revision, obtain the separate timeline approval fingerprint, and render/verify the exact master. A changed matte or font invalidates that approval. The renderer encodes the selected shot(s), title(s), masks, and audio once in the supported SDR path. Publishing remains a separate request.
