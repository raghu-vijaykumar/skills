# Reusable 4K CTA and HLG vlog composition

**Created:** 2026-11-09
**Status:** Implementation complete; exact-master creative review pending
**Input:** Create a reusable Like, Share, Subscribe stock animation inspired by a supplied example, replace the veg palav closing CTA and `ONE BY ONE` wording, and prepend the channel intro.

## User scenarios

1. **Reusable animation (P1):** An editor generates an original UHD transparent CTA stock clip for another video without copying the reference footage or sound.
2. **Veg palav update (P1):** The editor rebuilds graphics from the clean HLG source, retaining the other cues while changing the ingredient heading, and places the new CTA at the closing beat.
3. **Intro and delivery (P1):** The editor prepends the five-second SDR channel intro to the HLG cooking video and reviews one output with synchronized original soundtracks.

## Requirements

- Generate a 3840×2160 transparent, five-second, 30 fps CTA with Like, Share, Subscribe, Subscribed, and bell states. Allow a reusable placement option. The design must be original and source-independent.
- Keep the cue renderer's existing default ingredient heading and CTA behavior for earlier projects, while allowing an edited heading such as `INGREDIENTS`.
- Represent the clean source, intro, cue sheet, CTA asset, start time, color conversion, audio policy, and output settings in a validated, versioned manifest. Bind final render approval to that manifest and input hashes.
- Reject missing, changed, mismatched, or unsupported inputs before a full render. Preserve source and existing preview files.
- Compose the intro, revised ASS graphics, and transparent CTA in one HLG-base HEVC Main10 delivery encode. Carry the two source soundtracks in sequence without CTA sound.
- Explain that a re-encoded composite omits the clean source's Dolby Vision RPU. Do not claim Dolby Vision preservation.
- Produce bounded intro, ingredient, and closing previews and exact-master verification evidence. Human review is required for placement, color, motion, and audio.
- Do not include generated media in Git or publish the video.

## Acceptance

- The reusable asset probes as 3840×2160 at 30 fps with an alpha channel, and sampled states show the requested visual sequence.
- Veg palav frames at 0:22 contain the remaining ingredient cards and `INGREDIENTS`, with no `ONE BY ONE`. Frames at the end have the new stock CTA and no old CTA cards.
- The intro occupies the first 150 output frames. The main starts at 5.0 seconds. Expected output duration is approximately 502.7 seconds.
- The output probes as 3840×2160, 30 fps, 10-bit BT.2020/HLG with 48 kHz stereo audio. Affected picture and sound are reviewed from the exact output.
- Focused tests, documentation checks, and rendered preview review pass.

## Assumptions

- The supplied stock file is a visual reference, not a licensed asset to copy.
- The existing `1793705008095816.mp4` and cue sheet are the clean edit and overlay source for the baked HLG-base preview.
- The five-second intro is prepended without an overlap transition. The new CTA runs over clean-source time 482–487 seconds.
