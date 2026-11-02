# AutoCut preview (initial implementation)

Run:
```bash
python content-studio/skills/content-studio-autocut/scripts/autocut.py --folder ./raw --duration 12m --output ./rough-cut
```

Optional `--annotations annotations.json` or `--transcripts transcript.json`:
```json
{"segments":[{"source":"clip01.mp4","start":10,"end":24,"score":0.9,"reason":"Opening hook","text":"We just arrived"}]}
```

**Important:** This first implementation generates a **silent video preview**. It does not yet preserve or mix source audio, automatically transcribe, detect scene cuts, score visual quality, or call a vision-language model. Without annotations, it samples footage at fixed intervals. The exported timeline is intended for manual review, not publishing. FFmpeg/FFprobe are required. It uses source-file order, not verified capture timestamps. The script is not yet integrated into the global installer.
