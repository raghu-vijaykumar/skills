# IndicF5 narration backend

Validated local settings for cloned Kannada narration. Weights, virtual
environments, reference audio, and rendered media stay outside Git.

## Model choice

- `ai4bharat/IndicF5` (0.4B, MIT): zero-shot cloning for 11 Indian languages,
  including Kannada, from a short reference clip plus its transcript.
- As of November 2026 no larger open model combines Kannada with voice cloning.
  `bodhan-ai/indic-speak` (3B) has stronger Kannada TTS but no cloning, and
  Mistral Voxtral TTS (4B) clones but does not support Kannada.

## Defaults

| Setting | Value | Notes |
| --- | --- | --- |
| `nfe_step` | `32` | Quality default. `16` only for quick drafts or timing tests. |
| `cfg_strength` | `2.0` | Classifier-free guidance. |
| `sway_sampling_coef` | `-1.0` | Library default. |
| `speed` | `1.0` | Do not bake pacing into synthesis. Fit timing separately with bounded `atempo`. |
| Sample rate | `24000` Hz mono | Model output rate. |
| `target_rms` | `0.1` | Library default. |
| Reference audio | 10-15 s, one speaker, clean | Must match the reference transcript exactly. |
| Internal cross-fade | `0.15` s | Used when long text is split into inference chunks. |
| Timeline tempo cap | `1.12` | Never exceed it to hide a script/runtime mismatch. |

Render at `nfe_step=32` unless the user explicitly asks for a draft. Doubling
steps roughly doubles render time and is the accepted quality trade-off.

## Loader caveats

The published `model.py` leaves the checkpoint loading lines commented out, so
the documented `AutoModel` path can produce random or generic weights. Load the
released weights directly:

- Read `model.safetensors` and keep keys with the `ema_model._orig_mod.` prefix
  after stripping that prefix.
- Drop the `mel_spec.mel_stft.*` buffers that the CFM model does not own.
- Assert `missing == 0` and `unexpected == 0` (364 tensors for the released
  checkpoint) before inference.
- TorchAudio 2.11 routes `load()` through TorchCodec. If TorchCodec is absent,
  decode reference audio with SoundFile and return a tensor instead of
  installing another codec stack.

## Skill commands

```bash
# Render every section; resumable by text hash and render settings.
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" synthesize \
  --profile my-voice --script narration.json \
  --model-dir "/path/to/IndicF5" \
  --reference "/private/voice/reference.wav" \
  --reference-text "exact transcript of the reference clip" \
  --nfe-step 32

# Fit the rendered sections to the master and build a review preview.
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py \
  --workspace "/path/to/draft" assemble \
  --script narration.json --video "/path/to/master.mp4" --preview
```

The script JSON contains ordered `segments` with `id`, `start`, `end`, and
`text`. Outputs live under `<workspace>/.content-studio/voice/narration/`.
Synthesis refuses to run without an affirmed consent note. `assemble` needs
only FFmpeg; `synthesize` needs the IndicF5 environment.

## Pipeline

1. Enroll the speaker with `scripts/voice.py` and an explicit consent note.
2. Write the narration as timestamped sections. Keep the creator's source text,
   the TTS text, and the section start/end together.
3. Synthesize each section with `voice.py synthesize`. The manifest is keyed by
   text hash and render parameters, so interrupted runs can continue.
4. Round-trip transcribe the first sample and spot-check later sections. A
   clone that does not transcribe back to the input is not approved.
5. Fit each section with `voice.py assemble`, which applies at most 12%
   `atempo` and reports every overrun; do not silently speed up or trim the
   script.
6. `assemble` loudness-normalizes the track to `-16 LUFS`, true peak `-1.5 dBTP`.
7. Render the 1080p review preview and require a human listening review before
   the production mux or publication.

## Quality gates

- Consent is explicit and recorded in the profile manifest.
- The reference clip and its transcript are aligned and free of music or noise.
- Every generated section transcribes back to the intended words.
- No clipping; no unexplained tempo change above 1.12.
- Runtime overruns are listed with options: trim the script, extend the final
  frame, or start the section earlier.
- Synthetic speech is disclosed to viewers where appropriate.

## Known limits

- F5 predicts a fixed mel duration per chunk; very long text must be split
  (the library chunks at roughly 25 seconds of reference-scaled text).
- Best-of-N selection can improve a difficult line, but each extra take costs a
  full render.
- Fine-tuning on the creator's own footage is the next quality step; keep the
  base weights untouched and store adapters outside Git.
