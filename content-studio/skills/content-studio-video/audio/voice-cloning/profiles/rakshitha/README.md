# rakshitha voice profile

Consented Kannada–English voice profile bundled with the voice-cloning skill.

| Field | Value |
| --- | --- |
| Profile | `rakshitha` |
| Language | `kn-en` |
| Samples | 5 WAV files, 125.59 s total |
| Consent | Affirmed 2026-11-07 by the speaker/owner |
| Backend | IndicF5, `nfe_step=32`, `cfg_strength=2.0`, `speed=1.0` |

`profile.json` records the SHA-256 and duration of every sample. Do not edit a
sample without updating its hash.

## Use it

The skill looks for `--profile rakshitha` in the workspace first, then falls
back to this bundled folder. Outputs still go to the selected workspace.

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" status --profile rakshitha

python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" synthesize \
  --profile rakshitha \
  --script narration.json \
  --model-dir "/path/to/IndicF5" \
  --reference "content-studio/skills/content-studio-video/audio/voice-cloning/profiles/rakshitha/reference.wav" \
  --reference-text "$(cat content-studio/skills/content-studio-video/audio/voice-cloning/profiles/rakshitha/reference.txt)" \
  --nfe-step 32
```

On PowerShell, read the transcript as UTF-8:

```powershell
$ref = "content-studio/skills/content-studio-video/audio/voice-cloning/profiles/rakshitha"
$text = Get-Content "$ref/reference.txt" -Raw -Encoding utf8
```

## Files

- `sample-000.wav` … `sample-004.wav` — enrolled speech samples.
- `reference.wav` — 11 s clean reference clip for cloning.
- `reference.txt` — exact transcript of `reference.wav`; it must match.
- `profile.json` — consent record, sample hashes, and backend defaults.

## Privacy

This folder contains biometric voice data. It is committed to this repository at
the owner's request. Removing it later does not remove it from Git history.
Do not reuse this voice outside the owner's channels, and disclose synthetic
speech where appropriate.
