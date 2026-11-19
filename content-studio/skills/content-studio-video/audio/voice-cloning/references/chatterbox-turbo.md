# Chatterbox Turbo English narration backend

`en-raghu` and `en-rakshitha` use the local [Chatterbox Turbo](https://github.com/resemble-ai/chatterbox)
English checkpoint. Their consented reference WAVs are bundled in
[`profiles/en-raghu`](../profiles/en-raghu/README.md) and
[`profiles/en-rakshitha`](../profiles/en-rakshitha/README.md). The model's
[MIT-licensed weights](https://huggingface.co/ResembleAI/chatterbox-turbo)
and the Python environment remain outside Git.

## Tested environment

- Python 3.11, `chatterbox-tts==0.1.7`, and `setuptools<81`. The watermark
  package imported by this release still needs `pkg_resources`.
- CPU `torch==2.6.0` produced the reviewed short previews. CUDA is optional
  when the installed PyTorch build supports it.
- Official checkpoint revision:
  `749d1c1a46eb10492095d68fbcf55691ccf137cd`.
- Required local files: `t3_turbo_v1.safetensors`,
  `s3gen_meanflow.safetensors`, `ve.safetensors`, `tokenizer_config.json`,
  `special_tokens_map.json`, `added_tokens.json`, `vocab.json`, `merges.txt`.
  The default built-in `conds.pt` is optional for an owner-supplied reference.
  The older `s3gen.safetensors` is unused by Turbo's mean-flow decoder.

Use an isolated environment outside the repo:

```powershell
$voiceEnv = Join-Path $env:LOCALAPPDATA 'ContentStudio\envs\chatterbox-turbo'
uv venv --python 3.11 $voiceEnv
uv pip install --python (Join-Path $voiceEnv 'Scripts\python.exe') 'chatterbox-tts==0.1.7' 'setuptools<81'
```

Download the listed files from the pinned official checkpoint into a private
local model folder. The CLI's `--model-dir` points at that folder. It loads
weights with `ChatterboxTurboTTS.from_local` and never uploads the reference
audio. Run the CLI with the isolated environment's `python.exe`.

## Render a reviewed English script

```powershell
$voicePy = 'content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py'
& (Join-Path $voiceEnv 'Scripts\python.exe') $voicePy --workspace '<draft>' synthesize --profile en-raghu --script '<approved-script.json>' --model-dir '<local-model-folder>' --reference-variant take2 --device cpu --dry-run
& (Join-Path $voiceEnv 'Scripts\python.exe') $voicePy --workspace '<draft>' synthesize --profile en-raghu --script '<approved-script.json>' --model-dir '<local-model-folder>' --reference-variant take2 --device cpu
```

Choose `take3` for Raghu's other approved reference. For Rakshitha's selected
English voice, use `--profile en-rakshitha --reference-variant take2`. The
profile's hash check rejects missing, replaced, or out-of-folder reference
audio before the model loads. The segment manifest binds the reference variant
and hash to every output so a different take cannot reuse stale audio. The
existing `assemble` step requires exact scene review, real duration checks,
and 1.0x timing.

The owner liked both short test previews. That approves retaining both
references, not every future generated line. Round-trip transcribe each
scripted segment and listen for wording, speaker resemblance, pacing, and
mispronunciations before production use.
