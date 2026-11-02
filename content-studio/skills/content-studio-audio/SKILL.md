---
name: content-studio-audio
description: Master audio in a folder of videos, exporting mastered audio tracks and videos with the mastered audio muxed in.
---

# Content Studio Audio Mastering

Run `python <this-skill>/scripts/master.py --folder <video-folder>` to process all supported videos directly in a folder. Requires FFmpeg and FFprobe on PATH. Inputs are never overwritten. Outputs are written to `<video-folder>/audio-mastered/`: `<stem>.mastered.wav` (48 kHz stereo PCM) and `<stem>.mastered.mp4` (original video stream copied when MP4-compatible, mastered audio encoded as AAC). The script skips files without audio, reports failures per file, and emits `manifest.json` with source/output paths and loudness measurements. Review before replacing any existing production assets.

Default chain: high-pass 80 Hz, mild broadband denoise (afftdn), gentle compression (2:1), two-pass EBU R128 loudness normalization targeting -16 LUFS, 11 LU loudness range, -1.5 dBTP. This is suitable as a starting point for spoken-word vlogs, not a guarantee of studio-quality isolation. Preserve originals and avoid running on already mastered outputs. Use `--force` only to intentionally replace generated outputs. For music-heavy content or recordings with significant clipping, review manually. Video is copied without re-encoding when supported, preserving image quality and making rendering efficient. No clips are joined or trimmed.
