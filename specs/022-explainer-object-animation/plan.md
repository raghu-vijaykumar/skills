# Core Explainer object animation

The existing pilots use moving cameras and highlights over still hero art. The next private test uses independently animated objects, with camera movement optional. Use the existing Remotion scene authoring and preview routes.

| Test | Source range | Motion that must be visible with a fixed camera |
| --- | --- | --- |
| Payment opening | 0–3 s | A payment enters an exploded system. Layers separate, then pass the token down to a result. |
| Payment retry | 33–45 s | A request reaches the API, the response is lost, the same key returns the saved result, and the payment count stays at one. |
| Webhook | 84.5–91.5 s | A signature is typed, the event travels to the merchant, the server becomes unavailable, and repeated delivery attempts appear on a timeline. |
| Stale deploy opening | 0–12 s | The origin updates to v2, the browser requests the URL, and the cache returns v1. |

## Implementation and evidence

- Add frame-driven motion tracks and routed tokens to the existing Core Explainer motion primitives. Keep the choreography editable as Remotion source with scene-local frame numbers.
- Use original drawn geometry and new narration timed to these actions. Preserve each original full draft and master as the comparison baseline. The private previews cover the four ranges above.
- Profile the original masters with the workflow precheck. From the preview project run `python animation-review/audio.py`, `python animation-review/envelope.py`, and `node animation-review/render.mjs` (or add `--stills` for the native frame sweep). Estimate 2–8 minutes per preview from earlier renders. If a native render fails, use bounded native PNGs to fix the scene, then retry the MP4.
- Inspect fixed-camera start, action, and settled frames. Decode the full clips and check the exact audio cuts against the original speech. Compare synchronized baseline/new clips. Record any timing, legibility, or animation gap alongside the result.
- Deliver checked private previews, the reconstruction log, and reusable primitives with an example. Validate, review the staged diff, commit, and push the shared code. Approve a full production edit only after selecting the animation treatment from rendered evidence.

## Full reconstruction pass

The ranges below are working chapter boundaries from observation. Confirm individual cuts and cue points at 30 fps, starting from the source timecodes. Keep each shot's geometry, poses, edits, and audio cues editable. Use authored depth, eased joint angles, and word-level captions. Sample across each transition and compare the full narrated master by chapter after encoding.

| Reel range | Build and animate |
| --- | --- |
| 0–3 s | Badge drops onto its platform, plates separate, labels connect, and the reel cuts from dark to light. |
| 3–7 s | Globe turns, commerce nodes attach routes, transaction amounts travel, tally changes units. |
| 7–15 s | Card pushes forward, a redacted value enters the code strip, payment alerts duplicate, infrastructure replaces the phone. |
| 15–21 s | Product phone pushes into editable fields, the form submits, payment details leave the merchant frame. |
| 21–33 s | Draw vault rack and key store as separate objects. Follow the key and payment token through the cutaway. |
| 33–45 s | Phone tap, lost response, retries, two terminal panels, matching key, replayed response, one charge. |
| 45–58 s | Tokens travel from transaction to risk tree. Nodes illuminate along the route and the result selects a branch. |
| 58–69 s | Post the debit and credit independently, move the amount across, and settle at zero. |
| 69–80 s | Move the payment status into the event log, then distribute events through queue partitions. |
| 80–90 s | Animate the throughput and availability comparisons, then switch to request signing, delivery and retry marks. |
| 90–100 s | Increase the arrival rate. Add rows and counters on timed beats and preserve readable holds. |
| 100–106 s | Assemble the database rack from independently drawn cells. |
| 106–111 s | Split the rack and reveal additional partitions on a camera pullback. |
| 111–120 s | Tag traffic as hot or historical and move it through separate paths. |
| 120–128 s | Reassemble the system and trigger one staged motion per recap item. |
| 128–133 s | Pull the card into the agent interface and reveal the prompt. |
| 133–143 s | Type the command, resolve the recipient, show authorization, and update status and checkout in order. |
| 143–148.7 s | Bring the final interface in as a separate object and push into the resolved state. |

Acceptance follows the viewer experience: storyboard and full master cover the source duration and visible actions, cue drift and visual discrepancies are documented, actors remain distinct, and disclosure clearly separates illustrative architecture from verified claims. The private reconstruction uses newly authored picture and sound.
