# Cleanup method comparison

`previews/before.mp3` and `previews/after-afftdn.mp3` are real 7-second excerpts from a
synthetic text-to-speech voice mixed with pink noise, before and after `afftdn.py`.
They are not a private recording and not a claim of broadcast quality.

- `deepfilter.py`: neural speech denoise; choose only after comparing candidate audio.
- `afftdn.py`: FFmpeg adaptive denoise; used for the committed before/after.
- `keep_source.py`: explicit no-denoise route; keeps the source when it is already clean.

Every route may also write a blur review report. Compare WAVs and verify the exact
processed clip.
