# Rapid Take video style

Rapid Take is a video-only treatment for fast visual storytelling and satirical
commentary. Author the script, assets, voice and sound for the project.

## When to use it

Use Rapid Take for a story driven by quick visual associations, reveals, and
comic turns. It can carry a long-form technology story or explain a mechanism
at speed. Use Core Explainer when the viewer needs to inspect how each step works.

## Contract

- **Canvas:** 1920×1080 authored, 2560×1440 delivered, 30 fps.
- **Runtime:** 2–6 minutes. A 3–4 minute cut is the default.
- **Narration:** 195–215 words per minute. Short sentences. The joke lands at
  the end of the sentence, not in the setup.
- **Beats:** 2–5 seconds each. At least 55 distinct visual beats in a 3-minute
  cut. A beat can contain several independently timed object actions.
- **Sources:** every factual screen carries a visible `SOURCE` mark. A real
  screenshot must be a real capture. A typeset excerpt must say
  `TYPESET EXCERPT — NOT A SITE SCREENSHOT`.
- **Reactions:** archival or meme clips are `REACTION · NOT EVIDENCE`, never
  used to carry a factual claim. Their audio stays muted; the mix supplies the
  sting.
- **No fabricated dashboards.** Charts and diagrams may be authored schematics,
  but they must be labeled as illustration and must not invent measurements.

## Visual grammar

- Start with a vivid focal object, stage or lighting cue. Use a clear hue contrast,
  bright highlights and dark separation to direct the eye to the active object.
  Change color with the subject, action or punchline. Use the selected art
  preset's palette and preserve skin, material and source evidence readability.
  The house tokens include hot red for danger and acid yellow for punchlines.
- Full-bleed screenshots with a slow push-in; crop to the evidence, not the
  page chrome.
- Browser frames for documents and article captures.
- Give each frame one clear focal action. Keep the caption secondary to the action.
- Annotation boxes, circles, arrows, and underlines draw on in 6–10 frames.
  Use them to point at the evidence, not to decorate.
- Hard cuts, punch-ins, and one-frame flashes. Avoid slow crossfades.
- Meme cutaways are punctuation: 1–2.5 seconds, then back to the evidence.

## Choreograph from the recorded words

1. Record the original narration and align each spoken word's onset and end to
   the final audio. Audition the hook and punchlines at speed. Rewrite lines
   that have no clear action or image, then align the new take.
2. Inventory the on-screen heroes, supporting props, characters, poses, and
   handoffs. Use [real-world sources for the assets](../../../../review/critique/references/photo-reference.md),
   including photos of specific people for stylized portraits. Render each
   important asset and action in isolation before composing the shot.
3. Give every word an actor and a concrete event. Start a noun's reveal, a
   verb's action or a character's reaction on its word onset. A line such as
   “The clock runs. Think pizza” can cue the clock on “clock”, start the hand
   on “runs”, shift focus on “Think” and slide in the pizza on “pizza”. Short
   connecting words can advance an active action, such as a held reach moving
   into contact. Keep matched captions on the same clock.
4. Reuse the action plan across art presets. A photo-grounded character can have
   cel-shaded or pixel-art layers with the same gaze, wrist and expression
   targets. A clock can change shape, palette and texture while retaining its
   hand pivot and cue. Compile the cue-driven action tracks once and bind the
   [art preset](../../../../animation/videogen/scene-authoring/references/word-choreography.md)
   to those tracks for each render.
5. Check compiled actions against their word windows and validate the plan with
   `audit_word_cues.py` using `style: rapid-take` in the
   JSON plan. Recheck the exact render at the cue frames and at playback speed.
   With sound and captions off, verify that each hero reveal and the major
   action still read. Then verify the spoken word lands with the event.

## From a new long-form idea

1. Write the viewer promise and research the claims. Outline chapter payoffs
   and separate the factual mechanism from the comic analogy. For each joke,
   give the setup a visual the viewer recognizes and give the punchline its own
   object, action or reaction.
2. Pick a narrated proof with a real mechanism, a comic prop and a presenter
   reaction. Use the [shared scene authoring workflow](../../../../animation/videogen/scene-authoring/references/word-choreography.md)
   to build photo-grounded assets, prepare the rig, align the final take, and
   plan an event for every word. Set one vivid focal accent per active event.
3. Score the isolated heroes and the exact narrated proof. For variants, replay
   the same line and actor tracks through each art preset and inspect the same
   word, contact and held reaction. Revise the lowest axes against the relevant
   video or real-world evidence before extending the film.
4. Continue chapter by chapter. Track unresolved action and craft deficits in
   the draft and use the same cues, rig and palette rules through the full cut.
   Audit the assembled timeline, review seams and listen to the exact master
   at playback speed.

This route runs through scene authoring, narration timing, Remotion rendering
and critique. The agent authors the script, source-backed artwork and cue
bindings, then evaluates rendered evidence between revisions.

## Sound

- Narration is dominant. A low music bed may sit 14–20 LU below dialogue.
- Use short authored or cleared SFX for cuts, impacts, and reaction stings.
- Duck music at every factual statement; never let a joke mask a number.

## Reusable primitives

Import from `@raghu-vijaykumar/videogen/runtime/components/rapid-take/RapidTake`:

```tsx
import {RapidStage, Slam, StatSlam, SourceShot, BrowserFrame, MemeCut, Annotation, LowerThird, CutFlash} from '@raghu-vijaykumar/videogen/runtime/components/rapid-take/RapidTake';
import {RAPID_TAKE as R} from '@raghu-vijaykumar/videogen/runtime/design/rapidTake';
```

`MemeCut` must be placed inside a Remotion `<Sequence>` so the clip starts at
frame 0 instead of seeking to the global composition time.

## Beat sheet template

1. **Cold open (0–15s):** the absurd claim, one screenshot, one hard number.
2. **Receipt (15–40s):** who said it, when, and what they did not publish.
3. **Mechanism (40–110s):** scan → candidates → reproduction → exploits →
   distinct findings. One visual event per beat.
4. **Reality check (110–170s):** wrong-root anecdote, candidate patches,
   maintainer queue, the difference between a finding and a merge.
5. **Cost and limit (170–210s):** API cost, hypothetical bounty value, human
   review rate limit.
6. **Payoff (210–end):** discovery is not delivery; what a viewer should do.

## Review

- Render 3–4 short ranges before the full cut. Check the first second of every
  cut for a dead frame, clipped text, or an uncropped subject.
- Record cut and event cadence separately. Inspect quiet onsets, busy segments
  in consecutive frames, and object handoffs across cuts.
- Compare isolated actors and the exact delivery render. Score [appearance and
  motion](../../../../review/critique/references/object-scoring.md), including
  color separation in staging and sync in timing. Rerender and retest the lowest
  axes before extending the treatment through the full video.
- A source screenshot is evidence only if the capture is current and the claim
  matches the visible text. Otherwise mark the claim `REVIEW` or remove it.
