# Vlog workflow form

Fill the brackets and change **No** to **Yes** for the options you want.

- **Footage** — [raw folder or manual export path]
- **Stage** — [source prep | continue from manual edit | final review]
- **Channel or draft** — [optional]
- **Keep or avoid** — [shots, dialogue, HDR/Dolby Vision, other notes]

## Workflow in order

1. **Precheck** — Inspect footage and compatibility. Show the selected operations, exact commands, estimates, outputs, and fallbacks. **Human review** — Approve the current plan before edits.
2. **Raw folder handoff** — Preserve originals. Order clips, check duplicates, and deliver `.content-studio/_timeline.csv` plus `.content-studio/analysis/source-review/`. Run selected diagnostics in parallel where supported. **Human review** — Review findings, including blur evidence, and stop for my manual edit. Resume with my export and a new plan.

3. **Cut and lock picture** — With my manual export, settle cuts, intro, and transition overlaps first. **Human review** — Approve exact cut ranges, intro choice, and joins with sound.

   - **Trims or joins** — No. [Ranges or clip order]
   - **Blur fix · cut blurry spans** — No. [Ranges to keep or inspect]
   - **Fast pan cuts** — No
   - **Tilt cuts** — No
   - **Filler cuts · picture and audio** — No
   - **AutoCut** — No
   - **Intro video** — No. [File path | channel intro | show me candidates]
   - **Intro audio if used** — [keep | mute]
   - **Transitions** — No. [Joins and preferred effect]

4. **Build audio on the locked cut** — Extract boundary and middle frames for every cue, set frame-reviewed visual start/end, and check spoken meaning against the picture. **Human review** of script and timing before voice generation, then listen to every cue at 1.0x against its scene. Shorten and regenerate any line that runs past its visual end.

   - **Original dialogue and ambience** — Keep. [Keep | duck under narration | mute specific ranges]
   - **Source audio cleanup** — No
   - **Mute fillers in audio** — No. [Ranges, with picture timing kept]
   - **Draft voice script** — No
   - **Provide voice context** — No. [If Yes, places, events, personal observations, facts to include or avoid]
   - **Generate and mix narration** — No. [Recorded file | generated voice | consented clone]
   - **Language and tone** — [e.g. Kannada-English, conversational]
   - **Music** — No. [Track or mood]

5. **Correct picture, then assess upscale** — Use the completed edit with the requested audio. **Human review** — Compare bounded previews before choosing corrections or upscale.

   - **Stabilization** — No
   - **Color correction** — No
   - **HDR/Dolby Vision tone mapping** — No
   - **Upscale** — No. [Target resolution]

6. **Add graphics at delivery resolution** — Use times from the locked timeline after cuts and the intro. Preview selected effects.

   - **Scene overlays** — No. [Scenes and cues]
   - **Memes** — No
   - **Captions** — No

7. **Human review · Exact timeline** — Approve the revision, outputs, sound, and effect previews before final rendering.
8. **Render and review** — Render the approved revision. **Human review** — Check the exact master before packaging. Run archive independently. Publishing requires a separate explicit request.

   - **Thumbnail** — No
   - **Metadata** — No
   - **Archive** — No
