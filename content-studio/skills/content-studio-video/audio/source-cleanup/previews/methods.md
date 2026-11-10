# Cleanup method comparison

`before.mp3` is synthetic text-to-speech mixed with pink noise. The two
`after-*.mp3` files come from the same seven-second source encoded in a temporary
MP4. They are method outputs, not a private recording or a claim of broadcast quality.

- `deepfilter.py`: neural speech denoise. The committed candidate was generated
  with DeepFilterNet in a local Python 3.10 environment using `--speech-gain off
  --no-profiles`; its report returned `audio_review_required`. Listen for speech
  artifacts and residual noise before selecting it.
- `afftdn.py`: FFmpeg adaptive denoise; used for the committed before/after.
- `keep_source.py`: explicit no-denoise route; keeps the source when it is already clean.

To recreate the neural example, put the seven-second source in a temporary MP4,
make a temporary config whose `workspace` points to a writable directory, add the
DeepFilterNet virtual environment's `Scripts` directory to `PATH`, then run:

```powershell
python content-studio/skills/content-studio-video/audio/source-cleanup/scripts/deepfilter.py `
  --config <temporary-config.json> --path <temporary-source.mp4> `
  --out <temporary-output> --speech-gain off --no-profiles --force
```

Encode the resulting `audio-review/after.wav` to MP3 for the catalogue.

## Keep-source result

The same temporary source was run through `keep_source.py` with the same options.
Its report returned `status: ready` and `denoise_engine: skipped`. The audible
example is therefore the [unmodified input](before.mp3); this route intentionally
does not create a second denoised sample. Every route may also write a blur review
report. Compare WAVs and verify the exact processed clip.
