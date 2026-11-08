# Rapid Take video style

Rapid Take is the video-only satirical news treatment. It is a house style
inspired by high-velocity tech commentary, not a reproduction of another
channel. Do not reuse another creator's branding, scripts, music, thumbnails,
or graphics.

## When to use it

Use Rapid Take for a single technology story with a clear factual spine and room
for deadpan jokes. Use Tech Dispatch for carousels and posts, not video. Use
Core Explainer when the goal is to teach a mechanism without the news frame.

## Contract

- **Canvas:** 1920×1080 authored, 2560×1440 delivered, 30 fps.
- **Runtime:** 2–6 minutes. A 3–4 minute cut is the default.
- **Narration:** 195–215 words per minute. Short sentences. The joke lands at
  the end of the sentence, not in the setup.
- **Beats:** 2–5 seconds each. At least 55 distinct visual beats in a 3-minute
  cut. Never hold a static dashboard for a whole section.
- **Sources:** every factual screen carries a visible `SOURCE` mark. A real
  screenshot must be a real capture. A typeset excerpt must say
  `TYPESET EXCERPT — NOT A SITE SCREENSHOT`.
- **Reactions:** archival or meme clips are `REACTION · NOT EVIDENCE`, never
  used to carry a factual claim. Their audio stays muted; the mix supplies the
  sting.
- **No fabricated dashboards.** Charts and diagrams may be authored schematics,
  but they must be labeled as illustration and must not invent measurements.

## Visual grammar

- Near-black stage, white type, hot red for danger, acid yellow for punchlines.
- Full-bleed screenshots with a slow push-in; crop to the evidence, not the
  page chrome.
- Browser frames for documents and article captures.
- One idea per frame. A giant number or a single sentence beats a grid of
  cards.
- Annotation boxes, circles, arrows, and underlines draw on in 6–10 frames.
  Use them to point at the evidence, not to decorate.
- Hard cuts, punch-ins, and one-frame flashes. Avoid slow crossfades.
- Meme cutaways are punctuation: 1–2.5 seconds, then back to the evidence.

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
- Measure the final cut: median shot length ≤4s, detected cuts ≥55 for a
  3-minute video.
- Review the exact delivery render, not just the studio preview.
- A source screenshot is evidence only if the capture is current and the claim
  matches the visible text. Otherwise mark the claim `REVIEW` or remove it.
