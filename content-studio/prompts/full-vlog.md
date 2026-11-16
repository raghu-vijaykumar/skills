# Vlog workflow

## My input

- **Footage** — [raw vlog folder or manual export path]
- **Stage** — [source prep | continue from manual edit | final review]
- **Draft and channel** — [path or ID, optional]
- **Keep or avoid** — [must-keep shots, dialogue, HDR/Dolby Vision, or other notes]

## Choose operations

Change each **No** to **Yes** if I want that operation in the plan. For fixes, Yes requests diagnosis and a reviewable proposal. Apply only the changes I approve.

### Source fixes

- **Blur fix · cut blurry spans** — No
- **Fast pan cuts** — No
- **Tilt cuts · remove sustained camera roll** — No
- **Stabilization** — No
- **Source audio cleanup** — No
- **Color correction** — No
- **HDR/Dolby Vision tone mapping** — No

### Editing and delivery

- **Manual trims or joins** — No
- **AutoCut** — No
- **Draft voice script** — No
- **Generate and mix narration** — No
- **Remove fillers** — No
- **Music** — No
- **Upscale** — No
- **Transitions** — No
- **Scene overlays** — No
- **Memes** — No
- **Captions** — No
- **Thumbnail** — No
- **Metadata** — No
- **Archive** — No

## Workflow

1. **Precheck** — Identify the footage and stage. A raw folder defaults to source prep. If I supply only a manual export, inspect it and propose stages for my review. List selected and skipped operations. Give each selected operation a method ID, command, output, estimate, fallback, and review criterion.
2. **Human review · Plan** — Wait for my approval of the current plan before production. If the plan changes, show me the revision for approval.
3. **Raw folder · Source prep** — Use ordered originals as the handoff. Work from a copy when the input folder layout needs to stay intact.

   1. **In order** — Confirm capture times, flag uncertain timestamps, retain byte-identical duplicates in quarantine, and flag near-duplicates for review. Write the final capture order.
   2. **Baseline source review** — Inventory duration, dimensions, audio tracks, and HDR/Dolby Vision. Source prep includes blur evidence alongside the inventory. **Blur fix = No** keeps blurry spans out of the cut plan.

   3. **Parallel where supported** — Run only the selected specialist scans or diagnoses. For fast pans, blur cuts, and tilt cuts, show the proposed ranges. For stabilization, show likely crop. For audio, color, or tone mapping, compare a bounded preview with the original when useful.
   4. **Human review · Source handoff** — Show ordered originals, `.content-studio/_timeline.csv`, and reports in `.content-studio/analysis/source-review/`. For proposed cuts, let me review the exact ranges and any join previews with sound. Stop at the handoff for my manual edit. Approved proposals can carry forward to the later delivery timeline.
4. **Manual export · Continue when I supply it** — Fingerprint the export and start a new plan. I select only the stages I want.

   1. **Scope** — Use the selected operations and the supplied export. Map any selected source fixes to its timeline.
   2. **In parallel when independent** — Diagnose picture and audio. For voice, draft verified, timecoded narration from the exact edit and my context. Replace repeated long-scene descriptions with distinct, sourced facts or leave room for ambience.
   3. **Human review · Script and timing, if requested** — Show the text and cue timing before generating voice. For cloning, use only a consented profile when I explicitly request it. Preserve dialogue and ambience unless I approve a change.
   4. **In order** — If requested, compare bounded upscale candidates on the completed edit. Plan any selected upscale before delivery-resolution overlays. Bind voice and timed effects to the resolved picture timeline using supported methods.
   5. **Human review · Exact timeline** — Show proposed cuts, voice, effects, previews, output settings, and the revision fingerprint. Wait for my approval before the final render.
   6. **Human review · Exact master** — Check the complete picture and sound and the affected ranges with me. Prepare only the requested package items after review.

- Run archive independently when selected. Publishing requires my separate explicit request.
