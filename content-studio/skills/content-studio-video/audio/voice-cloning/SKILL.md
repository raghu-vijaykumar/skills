---
name: content-studio-video-voice-cloning
description: Use consented voice profiles for local English Chatterbox Turbo or Indian-language IndicF5 narration.
---
# Content Studio Voice

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

This skill uses a consented profile's declared backend: Chatterbox Turbo for the bundled English-only `en-raghu` profile, or IndicF5 for existing Indian-language profiles. It does not write scripts; use `content-studio-video-understand` for evidence-linked narration, then return here after the script and timing are approved. Weights, virtual environments, workspace reference audio, and production renders stay outside Git. The repo also tracks consented bundled profile references at their owners' explicit request. Backend setup and quality gates are in [Chatterbox Turbo](references/chatterbox-turbo.md) and [IndicF5](references/indicf5.md).

## Enroll (after the user supplies samples)

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" enroll --profile my-voice --samples "/private/voice/sample1.wav" "/private/voice/sample2.m4a" --language kn-en --consent --consent-note "I am the speaker and authorize cloning my voice for my vlogs"
```

Check enrollment:

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" status --profile my-voice
```

Requires FFmpeg and FFprobe. Each sample must have at least 3 seconds of audio and all samples together at least 20 seconds. The tool rejects missing, invalid and non-audio files. It never overwrites an existing profile. Workspace profiles live at `<workspace>/.content-studio/voice/profiles/<profile>/` and are normally kept outside Git. Bundled profiles under this skill's `profiles/<name>/` (for example `rakshitha`) are read-only fallbacks: `--profile` resolves the workspace copy first, then the bundled copy. A bundled profile contains consented biometric audio and is committed only at the owner's explicit request.

## Synthesize with IndicF5

Write the approved narration as a JSON script with ordered sections:

```json
{
  "segments": [
    {"id": "v01", "start": 0.0, "end": 14.0, "text": "ನಮಸ್ಕಾರ ಗೈಸ್! ..."},
    {"id": "v02", "start": 14.0, "end": 32.0, "text": "..."}
  ]
}
```

Render the clone with the enrolled profile and a clean 10–15 second reference clip:

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" synthesize --profile my-voice --script narration.json --model-dir "/path/to/IndicF5" --reference "/private/voice/reference.wav" --reference-text "exact transcript of the reference clip" --nfe-step 32
```

- `nfe_step=32` is the quality default; use `16` only for drafts.
- For a bundled profile, pass its `reference.wav` and `reference.txt` directly, for example `profiles/rakshitha/reference.wav`.
- Outputs: `<workspace>/.content-studio/voice/narration/segments/<id>.wav` and a resumable `manifest.json`.
- `--dry-run` lists reuse/render decisions. `--only v01,v02` limits the run. `--force` re-renders even when the text hash and settings match.
- Synthesis refuses to run without an affirmed consent note in the profile.
- The reference clip must be one speaker, free of music and noise, and its transcript must match exactly.
- For Kannada speech containing English words, keep the approved source text and
  write the IndicF5 synthesis text with those words phonetically in Kannada
  script. The default synthesis gate stops mixed Kannada/Latin cues before model
  loading; `--allow-mixed-script` is only for a bounded pronunciation sample
  that is round-trip transcribed and heard. A matching text hash or words/sec
  report proves timing and provenance, not intelligible speech.

## Synthesize English with en-raghu

The owner reviewed and retained both English reference takes. Choose one per
render; the CLI rejects an omitted choice so it cannot silently choose a voice
style. The same approved script and timeline format applies:

```powershell
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "<draft>" status --profile en-raghu
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "<draft>" synthesize --profile en-raghu --script "<approved-script.json>" --model-dir "<local-chatterbox-turbo-checkpoint>" --reference-variant take2 --device cpu
```

Use `--reference-variant take3` for the other approved clip. The profile binds
each choice to its committed SHA-256; a missing or changed clip stops before
model load. Chatterbox uses the audio reference directly, so English renders
do not take `--reference-text`. It needs an optional local Python 3.11
environment and official checkpoint outside Git; see
[setup and model requirements](references/chatterbox-turbo.md). Keep an English
script in Latin text. `--dry-run` validates the selection and reports reuse
without loading model weights. Chatterbox output is stored in the same
resumable segment manifest and uses the same review and assembly gates below.

## Assemble

Place the rendered sections on the frame-reviewed video timeline at their natural speed:

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" assemble --script narration.json --scene-review "/path/to/cue-scene-review/scene-review.json" --video "/path/to/master.mp4" --preview
```

For a timeline whose picture edit is planned but has not been rendered, use
`assemble --script narration.json --scene-review /path/to/scene-review.json --duration 952` to create the aligned voice
asset without a temporary full-length video. `--video` and `--duration` are
mutually exclusive. The duration-only route does not create a picture preview;
review bounded voice samples separately and use the approved delivery timeline
for the final picture and audio export.

- Probes each actual generated WAV, keeps every cue at its approved start and **1.0x** speed, and stops before mixing when speech exceeds its frame-reviewed visual end or crowds the next cue. Shorten the line and resynthesize it; never force a fit by speeding words up.
- Rejects an actual opening, intercue, or ending narration gap above five seconds by default. Use `--max-narration-gap` only when a longer music/ambience beat is explicitly planned and reviewed; cue duration estimates do not substitute for the measured WAV gap.
- Requires a completed `scene-review.json` for the exact script and picture. The review covers the meaning of the line as well as its start and end. A duration-only assembly validates the script review but needs later exact-picture verification.
- Writes `narration-24k.wav`, loudness-normalized `narration.wav` (`-16 LUFS`, true peak `-1.5 dBTP`), `timeline.json`, and an optional 1080p `preview.mp4`.
- With `--video`, the assembled WAV ends at the picture duration after checking that the last spoken cue ends inside it. The duration-only route retains its short voice-only tail for review.
- Assembly needs only FFmpeg; synthesis needs the selected backend environment.
- An overlong cue fails before preview encoding. Change the script and regenerate that cue at the accepted pace.

## Compare Indic-Mio emotions with a script

For a bounded, non-production comparison of Rakshitha's consented voice, run:

```powershell
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/indic_mio_compare.py
```

The script calls the open-source Speech Core LiteRT sidecar directly over
newline-delimited JSON; the Speech Studio UI is not involved. Its defaults
look for the sidecar and `libLiteRt.dll` together under
`%LOCALAPPDATA%/ContentStudio/tools/speech-core-v0.0.10/` and the downloaded
model under `%LOCALAPPDATA%/speech-core/soniqo__Indic-Mio-LiteRT/`.
Use `--sidecar`, `--bundle`, `--profile`, or `--output` to override those paths.
It checks consent and bundle completeness before rendering two fixed-seed
neutral/emotion pairs, then stores four WAVs, hashes, timing, and a manifest
in `%LOCALAPPDATA%/ContentStudio/voice-tests/indic-mio-rakshitha/<run>/`.
This is review evidence only; use a human listening review and the approved
production workflow before placing a voice in a video.

## Review gates

- Consent is explicit and recorded; never treat possession of a recording as consent.
- Round-trip transcribe the first section and spot-check later ones. A clone that does not transcribe back to the intended words is not approved.
- Check for clipping and mispronounced names; delivery tempo remains 1.0x.
- A human listening review is required before the production mux or publication. Synthetic speech is disclosed to viewers where appropriate.
- Only enroll voices owned by the user or cloned with explicit permission.
