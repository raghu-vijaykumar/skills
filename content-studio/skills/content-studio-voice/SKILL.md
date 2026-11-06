---
name: content-studio-voice
description: Bootstrap a consented personal voice profile from user-supplied samples for future vlog narration.
---
# Content Studio Voice

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

This skill is the **voice cloning bootstrap**, not an installed synthesis model. It enrolls and validates voice samples locally, normalizes them to 24 kHz mono WAV, and writes a profile manifest. It does not download models, clone speech, or produce voiceover yet.

## Enroll (after the user supplies samples)

```bash
python content-studio/skills/content-studio-voice/scripts/voice.py --workspace "/path/to/vlog-draft" enroll --profile my-voice --samples "/private/voice/sample1.wav" "/private/voice/sample2.m4a" --language kn-en --consent --consent-note "I am the speaker and authorize cloning my voice for my vlogs"
```

Check enrollment:

```bash
python content-studio/skills/content-studio-voice/scripts/voice.py --workspace "/path/to/vlog-draft" status --profile my-voice
```

Requires FFmpeg and FFprobe. Each sample must have at least 3 seconds of audio and all samples together at least 20 seconds. The tool rejects missing, invalid and non-audio files. It never overwrites an existing profile. Samples and the profile manifest live at `<workspace>/.content-studio/voice/profiles/<profile>/` and must be kept outside the Git repository or explicitly ignored.

## Later synthesis integration

Use a locally installed, license-reviewed multilingual voice cloning backend that supports the desired Kannada/English speech quality. Store backend settings and weights outside Git. The future synthesizer must verify consent, match the approved narration to the source video hash, produce timestamped WAV segments and a timing manifest, and require a human listening review. Preserve original dialogue where requested. Never substitute an unrelated voice or publish synthesized audio without approval.

Only enroll voices owned by the user or cloned with explicit permission. Do not treat possession of a recording as consent.
