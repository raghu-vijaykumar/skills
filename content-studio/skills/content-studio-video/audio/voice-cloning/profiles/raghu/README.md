# raghu voice profile

Consented English voice profile bundled with the voice-cloning skill at the
owner's request.

| Field | Value |
| --- | --- |
| Profile | `raghu` |
| Language | `en` |
| Samples | 3 WAV files, 721.02 s total |
| Consent | Affirmed 2026-11-08 by the speaker/owner |
| Source | Three local dictation recordings supplied by the owner |
| Backend | IndicF5, `nfe_step=32`, `cfg_strength=2.0`, `speed=1.0` |

`profile.json` records the SHA-256 and duration of every sample. Do not edit a
sample without updating its hash.

## Use it

The skill looks for `--profile raghu` in the workspace first, then falls back
to this bundled folder. Outputs still go to the selected workspace.

```bash
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" status --profile raghu

python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" synthesize \
  --profile raghu \
  --script narration.json \
  --model-dir "/path/to/IndicF5" \
  --reference "content-studio/skills/content-studio-video/audio/voice-cloning/profiles/raghu/reference.wav" \
  --reference-text "$(cat content-studio/skills/content-studio-video/audio/voice-cloning/profiles/raghu/reference.txt)" \
  --nfe-step 32
```

On PowerShell, read the transcript as UTF-8:

```powershell
$ref = "content-studio/skills/content-studio-video/audio/voice-cloning/profiles/raghu"
$text = [System.IO.File]::ReadAllText("$ref/reference.txt", [System.Text.Encoding]::UTF8).TrimEnd("`r", "`n")
```

## Files

- `sample-000.wav` … `sample-002.wav` — enrolled speech samples.
- `reference.wav` — 10.4 s clean reference clip for cloning.
- `reference.txt` — exact transcript of `reference.wav`; it must match.
- `profile.json` — consent record, sample hashes, and backend defaults.

## Reference transcript

> I'll explain as we go through the video. We are still in the Dubai Frame Museum.

## Privacy

This folder contains biometric voice data. It is committed to this repository at
the owner's request. Removing it later does not remove it from Git history.
Do not reuse this voice outside the owner's channels, and disclose synthetic
speech where appropriate.
