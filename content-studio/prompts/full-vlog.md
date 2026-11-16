# Vlog workflow

## My input

- **Footage** — [raw vlog folder or manual export path]
- **Stage** — [source prep | continue from manual edit | final review]
- **Draft and channel** — [path or ID, optional]
- **Keep or avoid** — [must-keep shots, dialogue, HDR/Dolby Vision, or other notes]

## Workflow

1. **Precheck** — Identify the footage and the requested stage. A raw folder defaults to source prep. If I supply only a manual export, inspect it and propose stages for my review. Give me an editable plan with method IDs, exact commands, outputs, estimates, fallbacks, and what I will review.
2. **Human review · Plan** — Wait for my approval of the current plan before production. If the plan changes, show me the revision for approval.
3. **Raw folder · Source prep** — Use ordered originals as the handoff. Work from a copy when the input folder layout needs to stay intact.

   1. **In order** — Confirm capture times, flag uncertain timestamps, retain byte-identical duplicates in quarantine, and flag near-duplicates for review. Write the final capture order.
   2. **Source checks · Parallel where supported**

      - **Media inventory** — Clip duration, dimensions, and audio-track presence.
      - **Blur** — Flag candidate spans and provide review evidence.
      - **Audio** — Check speech and ambience for cleanup needs.
      - **Stabilization** — Flag unstable motion and likely crop.
      - **HDR/Dolby Vision** — Identify clips needing preservation or a tone-map decision.
      - **Fast camera pans** — [skip | scan for candidate ranges].
      - **Sustained camera tilt** — [skip | scan for candidate ranges].
      - Compare a diagnosed issue with a bounded preview when useful.
   3. **Human review · Source handoff** — Show ordered originals, `.content-studio/_timeline.csv`, and reports in `.content-studio/analysis/source-review/`. Flag changes I may want to make. Keep the originals and deliver the handoff for my manual edit. Permanent source changes stay proposed for the later delivery timeline.
4. **Manual export · Continue when I supply it** — Fingerprint the export and start a new plan. I select only the stages I want.

   1. **Choose stages** — [review cuts and joins | diagnose audio/color/stabilization | draft voice script | generate and mix voice | assess upscale | add overlays or transitions | final review].
   2. **In parallel when independent** — Diagnose picture and audio. For voice, draft verified, timecoded narration from the exact edit and my context. Replace repeated long-scene descriptions with distinct, sourced facts or leave room for ambience.
   3. **Human review · Script and timing, if requested** — Show the text and cue timing before generating voice. For cloning, use only a consented profile when I explicitly request it. Preserve dialogue and ambience unless I approve a change.
   4. **In order** — If requested, compare bounded upscale candidates on the completed edit. Plan any selected upscale before delivery-resolution overlays. Bind voice and timed effects to the resolved picture timeline using supported methods.
   5. **Human review · Exact timeline** — Show proposed cuts, voice, effects, previews, output settings, and the revision fingerprint. Wait for my approval before the final render.
   6. **Human review · Exact master** — Check the complete picture and sound and the affected ranges with me. Prepare only the requested package items after review.

- **Optional requests** — [AutoCut | filler removal | music | memes | captions | thumbnail | metadata | archive | none]. Default to none. Publishing requires my separate explicit request.
