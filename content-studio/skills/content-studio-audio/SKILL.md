---
name: content-studio-audio
description: Master audio in a folder of videos, exporting mastered audio tracks and videos with the mastered audio muxed in.
---

# Content Studio Audio Mastering

Run `python <this-skill>/scripts/master.py --folder <video-folder> [--audio-only] [--cleanup]` to process all supported videos directly in a folder. Requires FFmpeg and FFprobe on PATH. Inputs are never overwritten. For a Content Studio draft, pass `--folder <draft>`; the script masters `<id>-final.mp4`, writes `<id>-audio-only.mp3` at the draft root, and puts `manifest.json` under `.content-studio/audio/`. Draft runs are always audio-only. For any other folder, outputs go to `<video-folder>/audio-mastered/` unless `--out` is supplied; add `--audio-only` to skip the mastered MP4. Outputs are `<stem>.mastered.wav` (48 kHz stereo PCM) and, without `--audio-only`, `<stem>.mastered.mp4`, plus `manifest.json` with source/output paths and loudness measurements. Review before replacing any existing production assets.

The default diagnoses integrated loudness and true peak. It normalizes only when the source is more than 1 LU from -16 LUFS or exceeds -1.5 dBTP; otherwise it exports audio without tonal processing with a `SKIP` decision. The two-pass EBU R128 correction targets -16 LUFS, 11 LU loudness range, and -1.5 dBTP. The output is remeasured and rejected if it misses the acceptance gate. The manifest records the issue, source and output measurements, decision, and validation. Changed audio gets ten-second before/after WAVs under the manifest's `previews/` folder. If requested cleanup misses the loudness gate, the command tries one loudness-only candidate, records the rejected attempt, and marks the result `REVIEW`.

`--cleanup` explicitly adds high-pass 80 Hz, mild `afftdn` denoise, gentle 2:1 compression, de-essing, and a gate for vlog dialogue. `--deess`, `--gate`, and `--arnndn-model <model>` request narrower effects; the model file must exist locally. These subjective cleanup effects remain `REVIEW` until a person listens to the before/after samples, even when loudness passes. Preserve originals and avoid running on already mastered outputs. Use `--force` only to intentionally replace generated outputs. Video is copied without re-encoding when supported. No clips are joined or trimmed.
