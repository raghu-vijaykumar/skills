---
name: content-studio-video-voice-cloning
description: Enroll a consented voice profile and synthesize cloned Kannada/English narration with local IndicF5.
---
# Content Studio Voice

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

This skill enrolls a consented voice profile and synthesizes cloned narration locally with IndicF5. It does not write scripts; use `content-studio-understand` for evidence-linked narration, then return here after the script and timing are approved. Weights, virtual environments, workspace reference audio, and production renders stay outside Git. The repo already tracks consented bundled profiles; a short synthetic gallery sample is also tracked. Settings, loader caveats, and quality gates are in [references/indicf5.md](references/indicf5.md).

## Enroll (after the user supplies samples)

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" enroll --profile my-voice --samples "/private/voice/sample1.wav" "/private/voice/sample2.m4a" --language kn-en --consent --consent-note "I am the speaker and authorize cloning my voice for my vlogs"
```

Check enrollment:

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" status --profile my-voice
```

Requires FFmpeg and FFprobe. Each sample must have at least 3 seconds of audio and all samples together at least 20 seconds. The tool rejects missing, invalid and non-audio files. It never overwrites an existing profile. Workspace profiles live at `<workspace>/.content-studio/voice/profiles/<profile>/` and are normally kept outside Git. Bundled profiles under this skill's `profiles/<name>/` (for example `rakshitha`) are read-only fallbacks: `--profile` resolves the workspace copy first, then the bundled copy. A bundled profile contains consented biometric audio and is committed only at the owner's explicit request.

## Synthesize

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

## Assemble

Place the rendered sections on the video timeline with bounded tempo changes:

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace "/path/to/vlog-draft" assemble --script narration.json --video "/path/to/master.mp4" --preview
```

- Keeps each section at its timestamp, applies at most `1.12` `atempo`, and reports every overrun in `timeline.json` instead of hiding it.
- Writes `narration-24k.wav`, loudness-normalized `narration.wav` (`-16 LUFS`, true peak `-1.5 dBTP`), `timeline.json`, and an optional 1080p `preview.mp4`.
- Assembly needs only FFmpeg; synthesis needs the IndicF5 environment.
- If narration extends past the video, the preview holds the final frame so the overrun is audible. Resolve it by trimming the script, extending the final frame, or moving the section earlier — do not raise the tempo cap.

## Review gates

- Consent is explicit and recorded; never treat possession of a recording as consent.
- Round-trip transcribe the first section and spot-check later ones. A clone that does not transcribe back to the intended words is not approved.
- Check for clipping, mispronounced names, and unexplained tempo changes above 1.12.
- A human listening review is required before the production mux or publication. Synthetic speech is disclosed to viewers where appropriate.
- Only enroll voices owned by the user or cloned with explicit permission.
