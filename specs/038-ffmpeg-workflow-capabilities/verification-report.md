# FFmpeg capability integration verification

**Date:** 2026-11-19
**Scope:** Eight Content Studio improvements inspired by `kajisho5/ffmpeg-skill`,
implemented in the existing canonical subskills. No upstream commit is pinned
and no external runtime dependency is installed.
**Production state:** Repository implementation is complete; no real draft was
edited, approved, published, or archived by this feature work.

## Process retained

The mandatory editable precheck and exact plan-hash approval still precede
production edits. Raw camera folders still stop after source preparation for a
human manual edit; AutoCut and captions remain explicit-request-only. Permanent
supported operations enter an immutable delivery timeline, require separate
human approval, and render one final picture/audio export. Exact-master review
and separate publication authorization remain in place. An unsupported
combination fails validation instead of silently falling back to an extra
full-master pass.

## Eight-story audit and feedback loops

| Story and owner | Identify and baseline | Bounded candidate or decision | Review and delivered feedback | Current limit |
| --- | --- | --- | --- | --- |
| 1. Preflight diagnostics — `content-studio-workflow` | Hash source; list every stream, display rotation, sampled frame timing, color, system capacity and selected FFmpeg components. | Choose available method, pilot a bounded sample, or mark missing/unknown method `UNSUPPORTED` and select a fallback. | Human approves the exact plan; checklist stores issue evidence; actual graph and final output still need validation. | Listing availability does not prove the full FFmpeg graph runs. |
| 2. Exact-master inspection — `review/final-render` | Hash delivered bytes; measure format, color, LUFS, true peak, black, freeze, flash, silence and destination guides. | An intentional beat closes as reviewed `SKIP`; a suspected defect receives a bounded timeline fix. | Every finding starts `REVIEW`; a fix needs new timeline approval, rerender and inspection of the new hash. | Detectors cannot judge creative intent or certify that an intentional still is wrong. |
| 3. Requested captions — `edit/captions` | Explicit request and approved cue sheet define the baseline of no caption operation; cue/font bytes are hashed. | Validate timing, text fit and font; generate ASS sidecar and bounded preview as `REVIEW`. | Human checks exact words, typography and safe zone; pending operation and separate timeline approval lead to one final encode; verify exact cue frames. | No automatic transcript or ordinary-vlog caption route. |
| 4. Recorder sync — `source/sync` | Hash camera/manual edit and recorder; correlate shared sound for offset, drift and confidence. | Short camera-left/recorder-right audition; ambiguous or silent cases stay `UNSUPPORTED`. | Human listens at early and late anchors; reanalyze against the supplied manual edit, then bind the reviewed report to one timeline audio cue and inspect exact-master sync. | One uncut SDR manual edit; uncertain long-clip drift cannot be assumed away. |
| 5. Portrait framing — `edit/clipping` and `edit/reframe` | Measure source context lost, supplied hero-box coverage/clearance and adjacent crop jumps. | Bounded crop proposals and source/crop/guide frames; no hero boxes gives `UNSUPPORTED` coverage. | Human chooses stable intervals and reviews phone-size motion; hashes bind crop evidence to the timeline; verify the delivered hero and audio boundaries. | Saliency is not semantic hero detection; HDR/DV picture route and smooth tracking remain unsupported. |
| 6. Final-mix loudness — `timeline` and `audio/mastering` | Analyze the resolved voice, music and source mix to null for baseline LUFS/true peak. | `SKIP` acceptable mixes; otherwise use measured loudnorm in one final audio encode. | Remeasure exact output; a target miss is `REVIEW`, with bounded retry or `SKIP` rather than a success claim; listen for balance and damage. | Measurement does not replace subjective mix review. |
| 7. Smart cut — `edit/clip-edit` | Baseline accurate cut reencodes all retained picture frames; source GOP plan estimates reusable packets. | `SKIP` if under half the picture can be copied; otherwise compare encoded boundary groups and copied interior H.264 GOPs. | Report source/candidate hashes, packet reuse, decoded-frame error and audio-join correlation; human reviews boundaries and exact master before selecting. Accurate cut is fallback. | Comparison only for tagged SDR, CFR, yuv420p H.264 with AAC or no audio; it is not a unified timeline adapter. |
| 8. Retime — `edit/retime` and `timeline` | Record source frame span, baseline duration, audio treatment and later cue positions. | Propose finite speed, freeze, reverse or loop span; `SKIP` effectively unchanged speed; shift downstream cues in a new revision. | Pending motion/sound review blocks fingerprint and final render. Test frame sequence/audio in a bounded preview; exact-master verify checks delivered frame count and saves picture/audio evidence. | Tagged SDR CFR H.264; adjacent joins and overlapping picture operations unsupported; old ASS sidecars/masks require regeneration. |

## Verification run

- `npm run check:docs`: **pass**, 186 maintained files, 1094 local links,
  72 canonical skills.
- Capability matrix checker: **pass**, 53 skill matrices, 164 methods,
  six explicitly unsupported methods.
- Focused Python suites: preflight **12**, exact-master **4**, captions **5**,
  recorder sync **3**, clipping/framing **9**, timeline **50**, and clip-edit
  **140** tests run (two clip-edit skips; all others passed). The smart-cut
  fixture specifically proves 230 retained frames, 177 byte-identical
  interior packets and three correlated audio windows. The retime fixtures
  compare every affected frame with its expected source frame and test source
  audio behavior, changed approval and exact-master review samples.
- Broad Node suite: **84 total**, **80 passed**, **4 skipped**, **0 failed**.
  The initial run exposed missing matrix declarations and LinkedIn social
  method routing under the stricter FFmpeg gate; both were corrected and the
  same suite passed.

Synthetic results establish the supported adapters and refusal behavior.
They do not count as approval of a real draft, subjective grading, caption
legibility, sync performance, or publication. For a real source, the editor
still records baseline evidence, bounded alternatives, human decisions and
the exact delivered-output result for each issue.
