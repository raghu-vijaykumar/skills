# Vlog workflow form

Fill the brackets and change **No** to **Yes** for the options you want.

- **Footage** — [raw folder or manual export path]
- **Stage** — [source prep | long cut from raw folder | continue from manual edit | final review]
- **Channel or draft** — [optional]
- **Keep or avoid** — [shots, dialogue, HDR/Dolby Vision, other notes]

## Workflow in order

1. **Precheck** — Hash and inspect footage, all streams, rotation, frame timing, color, machine capacity, and selected FFmpeg methods. Show the selected operations, exact commands, estimates, outputs, fallbacks, issue baselines, and review criteria. **Human review** — Approve the current plan before edits.
2. **Raw folder route** — Preserve originals. Order clips, check duplicates, and deliver `.content-studio/_timeline.csv` plus `.content-studio/analysis/source-review/`. Run selected diagnostics in parallel where supported. For **source prep**, review findings and stop for my manual edit. For **long cut**, use the [Long Cut form](long-cut.md) and [subskill](../skills/content-studio-video/edit/long-cut/SKILL.md): review blur, fast-pan, and tilt candidates and exact cut bounds, then assemble all retained footage in capture order. Long cut needs its own approved `edited-render` plan and timeline review before the one final render. Recheck any raw-clip recorder sync estimate against the supplied manual edit before using it there.

3. **Cut and lock picture** — For a manual export, settle cuts, intro, and transition overlaps first; the options below apply to that route. For long cut, use the reviewed ordered-source spans and options in the linked form. **Human review** — Approve exact cut ranges and joins with sound.

   - **Trims or joins** — No. [Ranges or clip order]
   - **Blur fix · cut blurry spans** — No. [Ranges to keep or inspect]
   - **Fast pan cuts** — No
   - **Tilt cuts** — No
   - **Filler cuts · picture and audio** — No
   - **AutoCut** — No
   - **[Retime](../skills/content-studio-video/edit/retime/SKILL.md) · speed, freeze, reverse, or loop** — No. [Exact range, factor/hold/count, and source-audio treatment; review shifted later cues]
   - **[Smart-cut comparison](../skills/content-studio-video/edit/clip-edit/references/smart-cut.md)** — No. [Cuts-only compatible SDR H.264 source and ranges; compare with accurate cuts before deciding. Candidate evidence only, not a delivery-timeline operation.]
   - **Intro video** — No. [File path | channel intro | show me candidates]
   - **Intro audio if used** — [keep | mute]
   - **Transitions** — No. [Joins and preferred effect]

4. **Build audio on the locked cut** — Extract boundary and middle frames for every cue, set frame-reviewed visual start/end, and check spoken meaning against the picture. **Human review** of script and timing before voice generation, then listen to every cue at 1.0x against its scene. Shorten and regenerate any line that runs past its visual end.

   - **Original dialogue and ambience** — Keep. [Keep | duck under narration | mute specific ranges]
   - **[Separate recorder sync](../skills/content-studio-video/source/sync/SKILL.md)** — No. [Recorder path; audition early and late alignment against the supplied manual edit]
   - **Source audio cleanup** — No
   - **Mute fillers in audio** — No. [Ranges, with picture timing kept]
   - **Draft voice script** — No
   - **Provide voice context** — No. [If Yes, places, events, personal observations, facts to include or avoid]
   - **Specifics needed for narration** — [e.g. ticket_status: unknown; give confirmed values and their source]
   - **Generate and mix narration** — No. [Recorded file | generated voice | consented clone]
   - **Language and tone** — [e.g. Kannada-English, conversational]
   - **Music** — No. [Track or mood]

   Diagnose the resolved final mix for loudness and true peak. Keep an acceptable mix as `SKIP`; preview a needed correction and verify the exact delivered audio before marking it `FIX`. Listen for voice clarity, balance, and pumping.

   Keep an unconfirmed specific as `unknown` in the prompt. Ask for it or omit the dependent claim from the spoken script; do not infer ticket purchase, admission, or price from footage alone.

5. **Correct picture, then assess upscale** — Use the completed edit with the requested audio. **Human review** — Compare bounded previews before choosing corrections or upscale.

   - **Stabilization** — No
   - **Color correction** — No
   - **HDR/Dolby Vision tone mapping** — No
   - **Upscale** — No. [Target resolution]

6. **Add graphics at delivery resolution** — Use times from the locked timeline after cuts and the intro. Preview selected effects.

   - **Scene overlays** — No. [Scenes and cues]
   - **Memes** — No
   - **[Requested captions](../skills/content-studio-video/edit/captions/SKILL.md)** — No. [Approved words, final-picture cue times, language, font, and safe-area treatment; review the bounded preview and exact master]

7. **Human review · Exact timeline** — Approve the revision, outputs, sound, and effect previews before final rendering.
8. **Render and review** — Render the approved revision. Inspect the exact output hash, format, color, loudness, black/freeze/flash/silence candidates, and portrait safe-zone guides where relevant. **Human review** — Check actual picture and sound before packaging. For every finding, record the baseline and acceptance criterion, try a bounded fix or reviewed `SKIP`, then inspect the newly approved and rendered master. Keep unresolved findings as `REVIEW` or `UNSUPPORTED`. Run archive independently. Publishing requires a separate explicit request.

   - **Thumbnail** — No
   - **Metadata** — No
   - **Archive** — No
