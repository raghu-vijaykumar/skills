# Content Studio AutoCut

Run:

```bash
python content-studio/skills/content-studio-autocut/scripts/autocut.py \
  --folder ./preprocessed --duration 12m --output ./.content-studio/rough-cut \
  --deliver ./<id>-rough-cut.mp4 \
  --orientation landscape --fit blur \
  --auto-transcribe --detect-scenes --auto-vision --quality-score
```

Preprocess raw camera clips first with `content-studio-videopreprocess`, then stage the per-clip `final.mp4` exports in a flat folder such as `.content-studio/autocut-input/`. AutoCut scans only the top level of `--folder`. Write `--output` to `.content-studio/rough-cut/` and use `--deliver <draft>/<id>-rough-cut.mp4` for the root deliverable.

`--orientation` filters clips by measured width/height. Use `--include-mismatched` or `--allow <filename>` for intentional exceptions. `--fit blur` (default) centers a mismatched clip over a blurred copy of itself instead of black bars; `--fit crop` fills the frame and crops; `--fit pad` uses black bars.

## Portrait deliverables from landscape footage

Use the same blurred-background fit as portrait clips in a landscape edit. The landscape clip stays centered at full width with horizontal blurred bands above and below:

```bash
python content-studio/skills/content-studio-autocut/scripts/autocut.py \
  --folder ./preprocessed --duration 60s --output ./rough-cut \
  --size 1080x1920 --orientation portrait --include-mismatched \
  --fit blur --detect-scenes
```

`--fit blur` is already the default; it produces horizontal blurred bands for a landscape source in a portrait target, matching the vertical blurred bands used for a portrait source in a landscape target.

### Subject-aware reframe (experimental)

**Experimental.** Use this only when the user explicitly asks for a subject-aware crop instead of the blurred bands.

```bash
python content-studio/skills/content-studio-autocut/scripts/autocut.py \
  --folder ./preprocessed --duration 60s --output ./rough-cut \
  --size 1080x1920 --orientation portrait --include-mismatched \
  --fit reframe --reframe-mode auto --subjects ./subjects.json \
  --detect-scenes
```

`reframe` uses AI subject boxes first, then saliency, then center. Each selected segment gets a stable crop and `reframe-preview/shot-*/reframe-review.html`. Read [the portrait reframe workflow](references/reframe.md).

Requires FFmpeg and FFprobe. For local visual analysis install Ollama, pull a vision model such as `ollama pull llava`, and use `--auto-vision` (or `--vision-model <model>`). For automatic speech transcription install `faster-whisper` (`pip install faster-whisper`); the selected Whisper model may download on first use. Without `--auto-transcribe`, supply a timestamped transcript using `--transcripts`. Optional semantic judgments from a vision/LLM model can be supplied as `--annotations`:

```json
{"segments":[{"source":"clip01.mp4","start":10,"end":24,"score":0.9,"reason":"Opening hook","text":"We just arrived"}]}
```

Outputs: `.content-studio/rough-cut/rough-cut.mp4` with original clip audio (or silence when absent), `edit-timeline.json`, `edit-timeline.html`, `timeline.otio`, `timeline.json`, `edit-decisions.json`, `review.html`. `--deliver` copies the rough cut to the root. The edit timeline lists each source contribution in final master order. Video is re-encoded to the highest source resolution (or `--size WxH`) H.264 SDR, audio to AAC.

**Known gaps:** Vision inference is now optional via Ollama; its subjective relevance score is not a calibrated visual-quality measurement. An optional exposure/sharpness heuristic is available with `--quality-score` (`pip install numpy`); motion stabilization and calibrated perceptual quality scoring remain pending. Scene-change detection is a technical signal, not understanding of the footage. Without transcripts or annotations the rough cut remains a heuristic sample. Story ordering follows filename order, not verified capture timestamps. Reframing uses one stable crop per selected segment; dynamic subject tracking is pending. Review the timeline before publishing. The installer now registers this skill, but existing versioned installations may require a package version bump to refresh the bundle.

## Editable canonical timeline (experimental)

The first rough-cut run now creates `timeline.json` and immutable `timeline-history/timeline-v001.json`. The FFmpeg renderer consumes the timeline; unchanged source segments are reused from `render-cache/`.

To apply deterministic changes, create `edits.json`:
```json
[
  {"action":"trim","id":"v0000","source_in":5,"source_out":12},
  {"action":"move","id":"v0002","index":0},
  {"action":"gain","id":"v0001","db":-4},
  {"action":"remove","id":"v0003"}
]
```

Run:
```bash
python scripts/timeline.py --output ./rough-cut --edits edits.json --render
python scripts/timeline.py --output ./rough-cut --rollback 1 --render
```

The video track is supported by the renderer, including embedded source audio and per-clip gain. Music and captions tracks are present as empty extensibility slots; **the renderer does not yet mix music, burn captions, or implement transitions**. Edits currently require structured JSON operations; translating natural-language feedback into these operations is a separate pending agent step. A revision render regenerates the contact sheet and audio samples and resets approval state after edits. Keep human approval before publishing.

## Agentic revisions from human feedback (experimental)

Run a local Ollama model (`ollama pull llama3.1`). The assistant proposes only validated remove/trim/move/gain operations, then writes `proposed-edits.json` for inspection:

```bash
python scripts/agent_edit.py --output ./rough-cut --feedback "Move the arrival shot to the beginning"
```

To explicitly apply the proposal, create a new timeline revision, rerender, and regenerate review assets:

```bash
python scripts/agent_edit.py --output ./rough-cut --feedback "Move the arrival shot to the beginning" --apply
```

The agent cannot yet create new B-roll clips, mix music, render captions, or interpret every natural-language request. Unsupported feedback produces an empty proposal. The `--apply` flag is an editing authorization, **not publishing approval**; a human must review the new media and approve separately.
