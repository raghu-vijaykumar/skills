# Operator route

The implemented CLI is documented in the [clipping skill](../../content-studio/skills/content-studio-video/edit/clipping/README.md). Commands for a real draft still require a media-specific preflight plan and human approvals.

1. Supply the finished long-form file, hero description, optional rough timestamp, intended portrait destination, and any desired duration or ending cue.
2. Inspect timestamped contact sheets and source audio. Review one contiguous candidate and set exact in/out. Save `selection.json` with the source hash and evidence.
3. Run the mandatory preflight profile and edit the plan for this actual draft. The plan names `content-studio-video-clipping` method `reviewed-hero-range`, reframe method `subjects` (or a reviewed alternative), and timeline method `crop`, with exact script arguments and a measured estimate. Obtain the editor's approval of that plan revision.
4. Preview the 9:16 framing beside the original at story and motion checkpoints. Revise the range or crop until the hero's action is readable.
5. Build and validate the immutable delivery timeline from the approved range and crop. Review its bounded composite and obtain separate approval of that exact timeline revision.
6. Render and verify the final portrait master, listen at the cut boundaries, inspect at phone size, and complete the preflight checklist. Ask separately before publishing.

Start with the clipping skill's read-only evidence and crop commands:

```powershell
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py inspect --source <long-form.mp4> --hero "main object and action" --start <in-seconds> --end <out-seconds> --out <draft>/.content-studio/clipping/selection-v001.json
python content-studio/skills/content-studio-video/edit/clipping/scripts/clipping.py propose-crop --selection <draft>/.content-studio/clipping/selection-v001.json --out-selection <draft>/.content-studio/clipping/selection-v002.json --output <draft>/.content-studio/clipping/crop-v001 --method subjects --subjects <hero-boxes.json> --size 1080x1920
```

The actual production preflight and timeline commands must use the supplied draft paths, selected timestamps, approved method IDs, and measured estimates. The selection format and timeline handoff are recorded in the [contract](contracts/selection.md).

For the first implementation test, use a synthetic landscape source with a moving colored hero, speech-like audio markers, and a second distractor. Check exact selected frames and audio span, visible hero coverage, stale-approval rejection, and source preservation.
