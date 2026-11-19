# Hero-led clipping capability

The first version selects one contiguous passage from one finished SDR video and frames it for a 9:16 Reel or Short. It creates review evidence and pending delivery-timeline changes; it does not authorize rendering or publication. The source remains untouched.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `reviewed-hero-range` | Supported | Finished SDR video + hero cue + reviewed source range and crop → source-linked selection and pending portrait timeline changes | Yes, after separate plan and timeline approval | [Rendered synthetic test](tests/test_clipping.py) and [evidence notes](previews/evidence.md) | One contiguous range; stable crop per interval; human story/framing review; no automatic hero recognition, smooth tracking, or HDR/Dolby Vision picture processing. |

## 1. Inspect the long-form source

Use the finished or approved export, not a raw camera folder. The editor may supply a rough range. Without one, `inspect` samples the whole source and leaves `selected` empty for manual choice. Source timestamps are absolute seconds in the original video.

```powershell
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py inspect --source <long-form.mp4> --hero "main object and action" --start <seconds> --end <seconds> --interval 5 --out <draft>/.content-studio/clipping/selection-v001.json
```

The command writes `selection-v001-source-review/evidence.json`, timestamped frames and contact sheets, plus `selection-v001.json`. Review the original sound near both boundaries. Edit `selected.source_in` and `selected.source_out` only after checking the actual picture and dialogue/action; a contact sheet alone cannot establish a complete beat. For a short hero appearance, sample the neighborhood more densely into a new selection revision path.

## 2. Propose and review portrait framing

Create normalized 0–1 hero boxes in the [reframe subject schema](../reframe/previews/example-subjects.json). The `source` value is the original filename, and each box has absolute `start`/`end` seconds. Prefer a box around the primary person, product, or mechanism and include its meaningful moving parts. If no reviewed box is available, explicitly choose `saliency` or `center` and judge that result on its merits.

For multiple heroes in one shot, add one box around the group with the highest confidence so the stable crop follows its center. Add a separately labelled, time-bounded box for each person or object as coverage evidence. The framing report checks every active box, including one that the crop proposal did not center on. A group box cannot prove individual visibility when subjects overlap or move between samples; inspect the whole preview. If their separation exceeds the portrait window, mark the proposal `REVIEW` and choose a shorter range, a reviewed crop interval, or another composition.

```powershell
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py propose-crop --selection <draft>/.content-studio/clipping/selection-v001.json --out-selection <draft>/.content-studio/clipping/selection-v002.json --output <draft>/.content-studio/clipping/crop-v001 --method subjects --subjects <hero-boxes.json> --size 1080x1920
```

Use `--start`/`--end` to propose shorter adjacent crop intervals within the selected passage. Each invocation writes a new selection revision, `reframe-review.html`, `framing-evidence.json`, and 5%/10% destination safe-zone guides. Review `minimum_hero_coverage`, `screen_center_motion`, and `context_lost_fraction`; a guide frame is sampled evidence, not proof that the subject stays framed throughout. `crop_boundaries` records each adjacent centre jump in destination crop widths and requires a human review note. All crop intervals must cover the chosen range without gaps before delivery. A static crop that loses the hero, a jump that distracts, or a shot needing wide context stays `REVIEW`/`UNSUPPORTED` until the editor chooses another treatment.

The editor reviews the source and crop at the start, middle, end, and every motion/shot change, then edits the final selection revision. Set `status` to `reviewed`; set `editorial_review.status` to `approved` with a reviewer and note covering story and sound boundaries; set each crop interval's `review_status` to `approved` with a `review_note`. The script never fills these approval fields. Validate the resulting record:

```powershell
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py validate --selection <reviewed-selection.json> --ready
```

## 3. Approve the production plan and build a timeline

Run `content-studio-workflow/scripts/preflight.py profile` on the actual draft and source, then `init --kind edited --stage edited-render`; edit `plan.json` before asking the editor to approve it. One step must identify route `content-studio-video-clipping` and method ID `reviewed-hero-range` with the exact `emit-changes` argv. Include the chosen reframe method, source hash, selected duration, 1080×1920 target, outputs, fallback, measured estimate, and phone-size/story/audio criteria. A plan revision needs new human approval. After approval, run `verify --phase start`.

Initialize a clean 9:16 SDR delivery timeline using the approved plan. Its FPS and output path are reviewed choices. The timeline must contain just the full source clip with source audio and no existing operations, audio cues, or transitions before the handoff.

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py init --plan <draft>/.content-studio/preflight/plan.json --source <long-form.mp4> --output <draft>/<id>-reel-v001.mp4 --timeline <draft>/.content-studio/timeline/reel-v001.json --width 1080 --height 1920 --fps 30
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py emit-changes --selection <reviewed-selection.json> --timeline <draft>/.content-studio/timeline/reel-v001.json --out <draft>/.content-studio/clipping/changes-v001.json
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py revise --timeline <draft>/.content-studio/timeline/reel-v001.json --plan <draft>/.content-studio/preflight/plan.json --changes <draft>/.content-studio/clipping/changes-v001.json --out <draft>/.content-studio/timeline/reel-v002.json --output <draft>/<id>-reel-v002.mp4
```

The emitted crop operations stay `pending_review` even when the source crop proposal was reviewed. Use `timeline.py validate` and a bounded `timeline.py preview` to inspect the composite and source audio. To approve, create a further immutable revision in which those exact crop operations have `review_status: approved`; get its fingerprint and a genuine human approval record as described in the [timeline skill](../../timeline/SKILL.md). Never change approval fields on an existing revision. `timeline.py render` encodes the approved source range, crop, and audio once, and `timeline.py verify` checks the exact result. Close the preflight checklist only after the editor watches the complete portrait master and listens at its cut boundaries.

## Current limits

- `inspect` creates visual discovery evidence, not an automatic semantic hero search. A rough timestamp or human contact-sheet review selects the moment.
- The crop analyzer computes one stable window per interval. Split into adjacent intervals for movement, but review visible jumps. Smooth tracked reframing is not implemented.
- The source must be SDR with a stable frame rate. HDR/Dolby Vision or high-bit-depth picture needs a separately designed and approved route. The delivery timeline also rejects those sources for portrait picture processing.
- The same source audio is trimmed with the picture. A silent input becomes a silent output audio track under the current timeline renderer; it is not described as original recorded sound.
- New voice, captions, music, SFX, or platform upload belong to separately reviewed Content Studio operations.
