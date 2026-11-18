# Verification: Earshot SFX workflow

## Shipped library

- Imported all 252 IDs from pinned Earshot commit `4ac3d2ac2b151e1c23376f9ce7f3047a17050013` as 48 kHz, 24-bit WAVs. The catalogue records each exact WAV hash, family, recipe, parameters, pinned bank version, recording credit, audit, and pending listening status.
- Earshot audit failed on 16 sounds. All 252 remain pending listening review and unavailable for an approved final cue until the relevant sound is listened to and approved. Five WAVs are mono; the others are stereo.
- Git ignores the older unknown-rights Reel SFX and new local creation candidates. The pinned bank subtree is tracked. New created sounds require an explicit rights and review decision before force-adding.

## Synthetic picture and audio evidence

- The 3-second Remotion fixture changed its card from “Idle” to “Clicked” at 1.0 s. The selector proposed `click/snap` at 0.9985 s with gain 0.4. `export-remotion` mounted it in the canonical entry, and a bounded Remotion render produced both video and audio. The encoded output measured approximately -91 dB at 0.20 s, -30.3 dB at 1.00 s, and -91 dB at 1.20 s; the reviewed frame at 1.10 s showed “Clicked.” This is timing evidence, not human creative approval.
- The SDR timeline fixture verifies an approved 880 Hz cue appears only after its reviewed start. The 10-bit HLG fixture uses the audio-only route and verifies identical coded video packet hashes, retained BT.2020/HLG stream metadata, zero video encodes, one mixed audio encode, and an 880 Hz cue at the intended time. No real Dolby Vision sample was supplied; delivery code compares Dolby Vision configuration when present and refuses mismatches.

## Gates

- SFX Python suite: 7 passed.
- Stock-library Python suite: 13 passed.
- Timeline Python suite: 35 passed.
- `npm test` with two temporary corrections to existing capability-table rows: 78 passed, 4 skipped, 0 failed. The committed baseline without those corrections has one capability-matrix failure.
- `npm run check:docs`: passed.
- `npm run check:capabilities` with those two temporary corrections: passed (48 matrices, 146 methods). Without them, the first failure is the preexisting voice-cloning row marked `Supported preview` instead of `Supported`; the next is a preexisting scene-review row without a local evidence link.

Automatic approval review rejected committing those unrelated table corrections directly to `main`, so they were restored and excluded from this feature. They need separate authorization or a separate maintenance task.
