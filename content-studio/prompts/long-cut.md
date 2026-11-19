# Long Cut workflow form

Use [Long Cut](../skills/content-studio-video/edit/long-cut/SKILL.md) when you want one long video from raw camera clips in capture order, with reviewed technical cuts. Fill the brackets and change **No** to **Yes** for the removals you want. Long Cut keeps usable footage and camera audio in sequence; it does not select a story or target duration like AutoCut.

- **Raw footage or draft** — [folder path]
- **Channel and draft ID** — [optional]
- **Order** — [capture order | supplied order with notes]
- **Keep or protect** — [important shots, speech, ambience, deliberate camera moves]
- **Output** — [landscape or portrait, resolution, frame rate; recommend if unsure]

## Workflow in order

1. **Precheck** — Inspect the channel, camera originals, machine capacity, and a bounded render benchmark. Show an editable `edited-render` plan with method IDs, exact commands and arguments, outputs, estimates, fallbacks, and review criteria. **Human review** — Approve the current plan before any source or draft edit.
2. **Order and diagnose** — Preserve originals. Confirm capture order and duplicate handling; create `.content-studio/_timeline.csv` and per-clip blur evidence. Scan every ordered clip for fast pans and camera tilt. Flag HDR/Dolby Vision, variable frame timing, rotation, and incompatible sources before promising a render.

   - **Remove blurry spans** — Yes. [Candidate ranges to protect or inspect]
   - **Remove fast pans** — Yes. [Intentional follow shots or whip transitions to protect]
   - **Remove camera tilt** — Yes. [Intentional angles or slanted scenery to protect]
   - **Other basic removals** — No. [Exact issue and source range; add a supported reviewed method to the plan]

3. **Human review · Cut decisions** — Show source-linked frames and bounded join previews with sound. For each candidate, record `cut` or `keep`, the reviewer and reason, and exact source-frame cut bounds. Do not remove footage from detector scores alone. Resume by building the ordered retained spans.
4. **Render the long-cut picture** — Build a native timeline from all retained spans, keeping camera audio aligned. Preview representative within-clip cuts, clip joins, and audio boundaries. Approve the exact timeline fingerprint, render a playable long-cut picture video, and verify its joins. **Human review · Video** — Watch and approve this video before narration starts.
5. **Prepare the full narration audio** — Use the approved picture to draft and validate narration internally. Record or synthesize the whole track, inspect every cue against its scene, and listen through the complete audio at normal speed. **Human review · Narration audio** — Let me listen to the full track and request timecoded changes; a written script is optional. Regenerate affected takes and repeat listening review until I approve the audio.

   - **Narration voice and language** — [recorded voice | generated voice | consented clone], [language and tone]
   - **Dialogue and ambience** — [keep | duck under narration | mute reviewed ranges]
   - **Music** — No. [Track or mood]

6. **Add narration, then graphics** — Put the approved narration on the locked picture and review the voiced video for timing and mix. After that, add requested motion graphics or ASS overlays using the same picture clock. Preview the narrated composite and approve the exact final timeline.

   - **Motion graphics** — No. [Scene cues, labels, and style]
   - **ASS overlays or requested captions** — No. [Words, cue times, font, and safe area]

7. **Final render and review** — Render and verify the exact final video with approved narration and overlays. Review picture, spoken audio, and every affected join. Return the long-cut video, narration audio, final video, and review evidence. Publishing requires a separate explicit request.
