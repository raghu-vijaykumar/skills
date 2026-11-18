# Planned operator route

This is an implementation guide for the proposed skill, not a production command set until the leaf is built and validated.

1. Supply the finished long-form file, hero description, optional rough timestamp, intended portrait destination, and any desired duration or ending cue.
2. Inspect timestamped contact sheets and source audio. Review one contiguous candidate and set exact in/out. Save `selection.json` with the source hash and evidence.
3. Run the mandatory preflight profile and edit the plan for this actual draft. The plan names `content-studio-video-clipping` method `reviewed-hero-range`, reframe method `subjects` (or a reviewed alternative), and timeline method `crop`, with exact script arguments and a measured estimate. Obtain the editor's approval of that plan revision.
4. Preview the 9:16 framing beside the original at story and motion checkpoints. Revise the range or crop until the hero's action is readable.
5. Build and validate the immutable delivery timeline from the approved range and crop. Review its bounded composite and obtain separate approval of that exact timeline revision.
6. Render and verify the final portrait master, listen at the cut boundaries, inspect at phone size, and complete the preflight checklist. Ask separately before publishing.

Existing read-only building blocks for step 2 and step 4 are:

```powershell
python content-studio/skills/content-studio-video/review/understand/scripts/understand.py --video <long-form.mp4> --out <draft>/.content-studio/clipping/source-review --interval 5
python content-studio/skills/content-studio-video/edit/reframe/scripts/subjects.py --input <long-form.mp4> --start <in-seconds> --end <out-seconds> --size 1080x1920 --subjects <hero-boxes.json> --output <draft>/.content-studio/clipping/crop-review
```

The actual production preflight and timeline commands must use the supplied draft paths, selected timestamps, approved method IDs, and measured estimates. The new clipping script proposed in the [contract](contracts/selection.md) does not exist yet.

For the first implementation test, use a synthetic landscape source with a moving colored hero, speech-like audio markers, and a second distractor. Check exact selected frames and audio span, visible hero coverage, stale-approval rejection, and source preservation.
