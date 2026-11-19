# Vlog workflow form

Fill the brackets and change **No** to **Yes** for the options you want.

- **Footage** — [raw folder or manual export path]
- **Stage** — [source prep | long cut from raw folder | continue from manual edit | final review]
- **Channel or draft** — [optional]
- **Keep or avoid** — [shots, dialogue, HDR/Dolby Vision, other notes]

## Workflow in order

1. **Precheck** — Hash and inspect footage, all streams, rotation, frame timing, color, machine capacity, and selected FFmpeg methods. Show the selected operations, exact commands, estimates, outputs, fallbacks, issue baselines, and review criteria. **Human review** — Approve the current plan before edits.
2. **Raw folder route** — Preserve originals. Order clips, check duplicates, and deliver `.content-studio/_timeline.csv` plus `.content-studio/analysis/source-review/`. Run selected diagnostics in parallel where supported. For **source prep**, review findings and stop for my manual edit. For **long cut**, use the [Long Cut form](long-cut.md) and [subskill](../skills/content-studio-video/edit/long-cut/SKILL.md): review blur, fast-pan, and tilt candidates and exact cut bounds, then assemble all retained footage in capture order. Recheck any raw-clip recorder sync estimate against the supplied manual edit before using it there.

3. **Create and approve the picture edit** — For a manual export, settle cuts, intro, and transition overlaps; the options below apply to that route. For long cut, use the reviewed ordered-source spans from step 2. Apply any requested picture correction or upscale before locking the picture. Render a playable picture edit with source sound and inspect the exact joins. **Human review · Video** — Watch and approve that video before narration work starts. A changed picture edit needs renewed video review and retimed narration.

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
   - **Stabilization** — No
   - **Color correction** — No
   - **HDR/Dolby Vision tone mapping** — No
   - **Upscale** — No. [Target resolution]

4. **Prepare the complete narration audio** — After video approval, extract boundary and middle frames for each cue, set frame-reviewed visual bounds, and check spoken meaning against the picture. Draft and validate the words internally, then record or synthesize a complete, playable narration track at natural speed. Listen through the whole track, checking pacing, pronunciation, repetition, silence, and each cue against its scene. Shorten and regenerate any line that runs past its visual end. **Human review · Narration audio** — Give me the full audio to listen to, with timecoded excerpts for requested changes. I do not need to read or approve a written script. Resume only after I approve the heard narration.

   - **Original dialogue and ambience** — Keep. [Keep | duck under narration | mute specific ranges]
   - **[Separate recorder sync](../skills/content-studio-video/source/sync/SKILL.md)** — No. [Recorder path; audition early and late alignment against the supplied manual edit]
   - **Source audio cleanup** — No
   - **Mute fillers in audio** — No. [Ranges, with picture timing kept]
   - **Draft narration internally** — Yes. [Share text only if I ask]
   - **Provide voice context** — No. [If Yes, places, events, personal observations, facts to include or avoid]
   - **Specifics needed for narration** — [e.g. ticket_status: unknown; give confirmed values and their source]
   - **Record or generate narration audio** — Yes. [Recorded file | generated voice | consented clone]
   - **Language and tone** — [e.g. Kannada-English, conversational]
   - **Music** — No. [Track or mood]

   Keep an unconfirmed specific as `unknown` in the prompt. Ask for it or omit the dependent claim from the spoken script; do not infer ticket purchase, admission, or price from footage alone.

5. **Add approved narration to the video** — Place the approved audio on the locked picture timeline, keeping requested dialogue and ambience. Preview the voiced video and check cue boundaries, speech clarity, music balance, loudness, and true peak. Keep an acceptable mix as `SKIP`; preview a needed correction and verify the exact delivered audio before marking it `FIX`. **Human review · Voiced video** — Listen and watch before graphics are added.

6. **Add motion graphics and ASS overlays** — Use the voiced video's locked picture times. Add only requested, supported graphics or ASS overlays, then preview the moving composite with narration before final timeline approval.

   - **Scene overlays** — No. [Scenes and cues]
   - **Memes** — No
   - **ASS overlays** — No. [Words, placement, cue times, and font]
   - **[Requested captions](../skills/content-studio-video/edit/captions/SKILL.md)** — No. [Approved words, final-picture cue times, language, font, and safe-area treatment; review the bounded preview and exact master]

7. **Human review · Exact timeline** — Approve the revision, outputs, sound, and effect previews before final rendering.
8. **Render and review** — Render the approved revision. Inspect the exact output hash, format, color, loudness, black/freeze/flash/silence candidates, and portrait safe-zone guides where relevant. **Human review** — Check actual picture and sound before packaging. For every finding, record the baseline and acceptance criterion, try a bounded fix or reviewed `SKIP`, then inspect the newly approved and rendered master. Keep unresolved findings as `REVIEW` or `UNSUPPORTED`. Run archive independently. Publishing requires a separate explicit request.

   - **Thumbnail** — No
   - **Metadata** — No
   - **Archive** — No
