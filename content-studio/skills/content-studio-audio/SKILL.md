---
name: content-studio-audio
description: Master audio in a folder of videos, exporting mastered audio tracks and videos with the mastered audio muxed in.
---

# Content Studio Audio Mastering

Run `python <this-skill>/scripts/master.py --folder <video-folder> [--audio-only] [--cleanup]` to process all supported videos directly in a folder. Requires FFmpeg and FFprobe on PATH. Inputs are never overwritten. For a Content Studio draft, pass `--folder <draft>`; the script masters `<id>-final.mp4`, writes `<id>-audio-only.mp3` at the draft root, and puts `manifest.json` under `.content-studio/audio/`. Draft runs are always audio-only. For any other folder, outputs go to `<video-folder>/audio-mastered/` unless `--out` is supplied; add `--audio-only` to skip the mastered MP4. Outputs are `<stem>.mastered.wav` (48 kHz stereo PCM) and, without `--audio-only`, `<stem>.mastered.mp4`, plus `manifest.json` with source/output paths and loudness measurements. Review before replacing any existing production assets.

Default chain: high-pass 80 Hz, mild broadband denoise (afftdn), gentle compression (2:1), two-pass EBU R128 loudness normalization targeting -16 LUFS, 11 LU loudness range, -1.5 dBTP. Add `--cleanup` for a de-esser and gentle gate on vlog dialogue; `--deess` and `--gate` enable them individually. `--arnndn-model <model>` uses RNNoise speech denoising instead of `afftdn`; the model file must exist locally. This is suitable as a starting point for spoken-word vlogs, not a guarantee of studio-quality isolation. Preserve originals and avoid running on already mastered outputs. Use `--force` only to intentionally replace generated outputs. For music-heavy content or recordings with significant clipping, review manually. Video is copied without re-encoding when supported, preserving image quality and making rendering efficient. No clips are joined or trimmed.
