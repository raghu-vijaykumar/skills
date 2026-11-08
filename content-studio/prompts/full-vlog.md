# Camera-footage vlog — Content Studio prompt

Input: `<raw-video-folder-or-manual-render>`
Requested stage: `<prepare clips | write voice script | generate and mix voice | assess upscale | add scene overlays | final review>`
Channel/draft and creative preferences: `<optional>`

If the input is a raw video folder and no stage is specified, **prepare clips only**. Stop and hand the individual clips to me for manual editing. If the input is a rendered edit and no stage is specified, inspect it and propose the next available stages without changing it.

Before any production edit, run `content-studio-workflow` precheck. Inspect the source, draft, and system; show an editable plan with the exact installed operation skill, method ID, script and arguments, inputs, outputs, estimate, fallback, and review criterion. Incorporate my changes and obtain approval of the current plan revision. A changed method or stage requires fresh approval. Check each requested method's `methods.json` before promising it.

## Stage rules

- **Prepare clips:** Order and deduplicate sources; diagnose audio, blur, stabilization, and HDR/Dolby Vision. Apply only approved source fixes. Preserve original footage, keep blur spans as review evidence, and hand off `drafts/<id>/.content-studio/processed-clips/` plus `.content-studio/_timeline.csv`. Do not make a joined master, story edit, narration, overlay, or upscale from a raw-folder request.
- **Manual edit:** I choose shots, trims, transitions, and story outside Content Studio. Record the supplied render's path and hash; use its timeline for all later work.
- **Voice script:** Analyze frames and audio from that render. Use verified evidence and my context for names, events, and opinions. Audit adjacent cues in long scenes for repeated descriptions; replace them with distinct, sourced facts about the place when relevant, or leave natural sound room. Keep source URLs in cue notes, distinguish general facts from what I actually did, and report uncertain claims. Stop for text and timing approval.
- **Voice:** Generate only from an approved script. Clone a voice only with my explicit request, consented samples, and a listening check. Preserve original dialogue and ambience unless I approve a specific mix change. Produce review audio and a separately reviewed voiced video with the narration mix script.
- **Upscale:** Only after any requested voice mix, assess the completed edited video. Compare untouched, Lanczos, and available AI previews on bounded ranges; estimate full runtime and check noise, flicker, detail, HDR/DV, and exact-output side effects. Skip if there is no worthwhile gain. Never batch-upscale the raw clips.
- **Scene overlays:** Only for scenes I identify. Verify cue times against the voiced/upscaled edit, preview each motion type, and render code-generated graphics at delivery resolution **after** upscale. Do not upscale the graphics.
- **Final review:** Inspect affected ranges and the full picture and audio, then prepare only the requested package items. Publication and archive are separate requests.

AutoCut is experimental and runs only if I explicitly request it. Do not mute speech, remove filler, add music, memes, captions, a thumbnail, or publish by default. If a method or backend is unavailable, report the gap and offer a supported route; do not claim an output was made.
