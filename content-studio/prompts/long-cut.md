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
4. **Assemble and preview** — Build one native delivery timeline from all retained spans, keeping camera audio aligned. Validate the output canvas and preview representative within-clip cuts, clip joins, and audio boundaries. **Human review · Exact timeline** — Approve the revision and fingerprint before final rendering.
5. **Render and review** — Render one long MP4, verify the exact delivered picture and sound, and review every flagged join. Return the video and review evidence. Publishing requires a separate explicit request.
