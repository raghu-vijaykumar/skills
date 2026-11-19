---
name: content-studio-video-long-cut
description: Assemble ordered camera originals into one long reviewable video after human-approved blur, fast-pan, and tilt removals. Use when the editor asks for a full-length technical cut rather than AutoCut story selection.
---

# Long cut

Use the [copy-and-edit Long Cut form](../../../../prompts/long-cut.md) to capture the editor's source, cut, and output choices.

Use this skill when the editor explicitly wants one continuous video from camera originals in capture order. Keep every usable source span in sequence. Remove only reviewed blur, fast-pan, and camera-tilt intervals. This is an editorial assembly, without AutoCut's transcript selection, story outline, target duration, or automatic shortening. Preserve original media and keep camera audio synchronized with the picture cuts.

## Plan and diagnose

Complete the mandatory [workflow precheck](../../../content-studio-workflow/SKILL.md) before changing the draft. Because the requested deliverable is a long rendered assembly from raw media, make an `edited-render` plan that explicitly includes source preparation, per-source scans, cut review, native timeline revision, one final render, and exact-master verification. Profile `prepare-clips`, `fastpan-scan`, `tilt-scan`, `long-cut-propose`, `long-cut-build`, and `timeline-delivery` as the selected method IDs. Show exact commands, sources, output size/rate, render estimate, fallback, and review criteria; get human approval of the current plan revision. Keep its checklist evidence. A changed plan needs renewed approval. Run the [source preprocessor](../../source/preprocess/SKILL.md) in analysis-only mode to create `original/`, `.content-studio/_timeline.csv`, and each clip's blur `review.csv`. Confirm the capture order and duplicate decisions with the editor.

Run the [fast-pan](../fastpan-cuts/SKILL.md) and [tilt](../tilt-cuts/SKILL.md) `scan` commands on **every** ordered source, writing one report per source to separate versioned scan folders:

```powershell
python content-studio/skills/content-studio-video/edit/fastpan-cuts/scripts/fastpan.py scan --input <ordered-original> --output <draft>/.content-studio/analysis/fastpan-long-v001/<clip-id>.json
python content-studio/skills/content-studio-video/edit/tilt-cuts/scripts/tilt.py scan --input <ordered-original> --threshold-deg 10 --sample-fps 1 --output <draft>/.content-studio/analysis/tilt-long-v001/<clip-id>.json
```

These scans are diagnostic; their scores cannot approve removals. For each candidate, inspect original footage, nearby frames, speech and natural sound. Blur may be intentional or low-detail; a pan may be a follow shot or transition; scene geometry can resemble camera roll. Use bounded join previews and inspect both sides of any proposed cut. Keep useful footage when uncertain.

The long-cut planner expects the canonical source review files and exactly one fast-pan and one tilt report for each source. It rejects stale reports and unsupported HDR/Dolby Vision picture cuts. The current native timeline encodes SDR only. Mixed source sizes or rates are normalized into the reviewed output canvas; inspect letterboxing and cadence in bounded previews. If any source needs an unsupported picture route, mark it `UNSUPPORTED` in the plan and stop before promising an export.

## Build the reviewed assembly

```powershell
$long = 'content-studio/skills/content-studio-video/edit/long-cut/scripts/long_cut.py'
python $long propose --draft <draft> --fastpan-dir <draft>/.content-studio/analysis/fastpan-long-v001 --tilt-dir <draft>/.content-studio/analysis/tilt-long-v001 --out <draft>/.content-studio/analysis/long-cut/proposal-v001.json
```

The proposal lists each source in capture order, its hash and frame count, and every blur/pan/tilt candidate with exact source-frame bounds and hashed evidence. It does not mark cuts approved. The human editor reviews each candidate and sets `decision` to `cut` or `keep`, `actor` to `human`, their `reviewer` name, and a substantive `review_note`. For a cut, adjust `cut_start_frame` and `cut_end_frame` to the reviewed source-frame boundaries; they must still overlap the detector candidate. The original `start_frame` and `end_frame` stay unchanged. Save that edited copy as a new review file. Do not create a human decision on the editor's behalf. Overlapping approved reasons become one removal; rejected candidates remain in the video. The plan and checklist must record the selected cut evidence and any `SKIP`/`REVIEW` decisions.

```powershell
python $long build --manifest <draft>/.content-studio/analysis/long-cut/review-v001.json --out <draft>/.content-studio/analysis/long-cut/changes-v001.json
```

`build` rechecks capture order, original bytes, detector evidence, complete candidate coverage, and human decisions. Its `changes.json` contains ordered retained source spans, no added transitions or graphics, and source-audio mixing for synchronized cuts. It cannot render by itself. Keep the proposal, review file, and changes file with the draft.

## Render and review

Use the [native delivery timeline](../../timeline/SKILL.md). `init` with the approved `edited-render` plan and the **first ordered original** (even if that clip is wholly removed later), then `revise` with `changes-v001.json`; set the reviewed output size/rate on `init` or in a later revision. Do not approve or render the uncut initial timeline.

```powershell
$timeline = 'content-studio/skills/content-studio-video/timeline/scripts/timeline.py'
python $timeline init --plan <draft>/.content-studio/preflight/plan.json --source <first-ordered-original> --output <draft>/<id>-final.mp4 --timeline <draft>/.content-studio/timeline/long-cut-v001.json --fps <output-fps> --width <output-width> --height <output-height>
python $timeline revise --timeline <draft>/.content-studio/timeline/long-cut-v001.json --plan <draft>/.content-studio/preflight/plan.json --changes <draft>/.content-studio/analysis/long-cut/changes-v001.json --out <draft>/.content-studio/timeline/long-cut-v002.json --output <draft>/<id>-final.mp4
python $timeline validate --timeline <draft>/.content-studio/timeline/long-cut-v002.json
python $timeline preview --timeline <draft>/.content-studio/timeline/long-cut-v002.json --start <join-time> --duration 5 --output <draft>/.content-studio/analysis/long-cut/join-preview-v001.mp4
python $timeline fingerprint --timeline <draft>/.content-studio/timeline/long-cut-v002.json
python $timeline render --timeline <draft>/.content-studio/timeline/long-cut-v002.json --approval <human-timeline-approval.json>
python $timeline verify --record <draft>/<id>-final.mp4.render.json --evidence-dir <draft>/.content-studio/timeline/long-cut-final-review
```

Run bounded previews on representative intra-clip cuts, inter-clip joins, portrait/landscape changes, and audio boundaries. The timeline revision is a proposal until the editor reviews its resolved spans, picture, audio, output settings, and fingerprint. Then use a genuine human timeline approval for `render`, followed by `verify` of the exact long video. No automatic publication.

For a long render, estimate duration from a representative benchmark and check free space. Use a resumable detached render with a durable log and completion marker when the host supports it. Keep source media and review evidence; remove only confirmed obsolete caches. If a join loses context, hurts speech, or the exact output fails review, revise the cut decisions and timeline, obtain fresh approvals, and render a new version.
