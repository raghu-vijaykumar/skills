# Content Studio AutoCut

Run:

```bash
python content-studio/skills/content-studio-autocut/scripts/autocut.py \
  --folder ./raw --duration 12m --output ./rough-cut \
  --auto-transcribe --detect-scenes --auto-vision
```

Requires FFmpeg and FFprobe. For local visual analysis install Ollama, pull a vision model such as `ollama pull llava`, and use `--auto-vision` (or `--vision-model <model>`). For automatic speech transcription install `faster-whisper` (`pip install faster-whisper`); the selected Whisper model may download on first use. Without `--auto-transcribe`, supply a timestamped transcript using `--transcripts`. Optional semantic judgments from a vision/LLM model can be supplied as `--annotations`:

```json
{"segments":[{"source":"clip01.mp4","start":10,"end":24,"score":0.9,"reason":"Opening hook","text":"We just arrived"}]}
```

Outputs: `rough-cut.mp4` with original clip audio (or silence when absent), `timeline.otio`, `edit-decisions.json`, `review.html`. Video is re-encoded to 1920x1080 H.264 SDR, audio to AAC.

**Known gaps:** Vision inference is now optional via Ollama; its subjective relevance score is not a calibrated visual-quality measurement. Dedicated blur/exposure/stabilization scoring remains pending. Scene-change detection is a technical signal, not understanding of the footage. Without transcripts or annotations the rough cut remains a heuristic sample. Story ordering follows filename order, not verified capture timestamps. Review the timeline before publishing. The installer now registers this skill, but existing versioned installations may require a package version bump to refresh the bundle.
