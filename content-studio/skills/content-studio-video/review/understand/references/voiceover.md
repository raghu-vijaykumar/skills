# Evidence-linked voiceover drafting

## Facts and evidence

- Read the contact sheets and the individual frames before writing a line.
- Cite the frame IDs that support each segment. `voiceover.py` rejects unknown IDs.
- Use the creator's context for names, dates, prices, travel times, and personal
  reactions. Footage alone does not prove them.
- Mark uncertain claims `needs_review: true`. If exhibit text, a sign, or a
  landmark is unreadable at the sampled resolution, describe only what is
  visible or ask the creator.
- Do not invent history, statistics, dialogue, or an event that happened between
  two samples.

## Context file

`--context` accepts a JSON object. Use it for creator-supplied facts that the
frames cannot prove:

```json
{
  "title": "Dubai Day 3",
  "language": "Kannada-English",
  "tone": "warm, excited, conversational",
  "itinerary": ["Cab from the hotel", "Dubai Frame", "Desert safari"],
  "facts_to_verify": ["Exact timestamps", "Museum exhibit names"],
  "pronunciation": {"Al Jaddaf": "al jad-daf"},
  "notes": "Silent master; voiceover can cover the full timeline."
}
```

## Language mix

- Write Kannada in Latin script by default (`namaskara`, `naavu`, `hogtiddvi`)
  unless the creator asks for Kannada script. It is easier to read on a
  teleprompter and avoids font problems in editing tools.
- Keep English for proper nouns and technical terms: Dubai Frame, Burj Khalifa,
  dune bashing, Sky View Observatory, desert safari.
- Mix at phrase level, not word level. A natural sentence sounds like:
  `Namaskara guys, ivattu namma Dubai trip day three. Premier Inn Al Jaddaf
  inda cab hattidvi, and the Dubai Frame is just nearby.`
- Avoid literary or formal Kannada in a casual vlog. Prefer the way the creator
  actually speaks. Keep sentences short enough to read in one breath.
- Use first-person plural (`naavu`, `namma`) for a shared trip. Use present tense
  for what is on screen and past tense for what just happened.
- Do not translate the same idea twice. One Kannada phrase plus one English
  phrase is enough.

## Timing

- A comfortable conversational pace is 2.4–3.2 words per second. The validator
  defaults to a hard maximum of 3.4 words per second.
- Leave 0.2–0.4 seconds between paragraphs for a breath. Do not fill every
  second; music and ambient sound need space.
- Start a line about half a second before the relevant visual, then let the
  scene land.
- If a line does not fit, split it across two segments or cut detail. Do not
  speed up the read.
- Keep a segment within one scene or one clear visual idea. A 60-second segment
  is usually too broad; 8–25 seconds is easier to review and retime.
- For a silent master, the voiceover can cover the whole timeline. For a master
  with dialogue, leave those ranges uncovered or explicitly mark them.

## Script schema

```json
{
  "title": "Dubai Day 3",
  "language": "Kannada-English",
  "source_sha256": "<copy from evidence.json>",
  "duration_seconds": 663.0,
  "approval": "pending",
  "segments": [
    {
      "id": "v01",
      "start": 0.0,
      "end": 18.0,
      "text": "Namaskara guys, ivattu namma Dubai trip day three...",
      "evidence_frame_ids": ["f0000", "f0001", "f0003"],
      "needs_review": false,
      "direction": "warm, excited, slightly fast",
      "notes": ""
    }
  ]
}
```

- `id` is stable across revisions.
- `start` and `end` are seconds in the approved master.
- `evidence_frame_ids` must exist in `evidence.json`.
- `needs_review` defaults to `true` when omitted, which prevents a clean pass.
- `direction` and `notes` are optional and are shown in `voiceover.md` but not
  in the teleprompter text.

## Validate and review

```bash
python content-studio/skills/content-studio-understand/scripts/voiceover.py \
  --input <workspace>/voiceover.json \
  --evidence <workspace>/evidence.json \
  --out <workspace> \
  --title "Dubai Day 3"
```

The report status is:

- `pass`: no schema, timing, or evidence errors and no review flags.
- `review`: no hard errors, but at least one warning or `needs_review` flag.
- `fail`: overlapping or out-of-range segments, unknown evidence frames, empty
  text, or speech over the pace limit.

The command exits non-zero on `fail`. Use `--allow-errors` only when you
deliberately want review files for a draft that still has errors.

Present `voiceover.md` and the report to the creator. Do not synthesize or
record until the exact text and timing are approved. If the master changes,
regenerate the evidence and retime the script.
