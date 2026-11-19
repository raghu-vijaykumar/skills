# Implementation Plan: en-raghu English Voice

**Branch**: `main` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

## Summary

Add the owner's two reviewed English reference takes as `en-raghu`, route that profile through a lazy Chatterbox Turbo backend in the existing `voice.py` command, and preserve the current IndicF5 path.

## Technical Context

- **Language/Version**: Python 3.11 for Chatterbox Turbo; existing CLI remains standard Python.
- **Primary Dependencies**: Optional `chatterbox-tts==0.1.7`, `setuptools<81`, FFmpeg/FFprobe.
- **Storage**: Two short WAV references and profile metadata in Git; model and output WAVs outside Git.
- **Testing**: Focused Python unit tests, documentation/capability gates, and one local-model English render.
- **Target Platform**: Windows CPU or CUDA environment with local model weights.
- **Constraints**: Consent, exact reference hashes, no cloud upload, no implicit production approval.

## Constitution Check

- One owning skill and script: pass.
- Portable workspace and model paths: pass.
- Real output validation: required by the test and review steps.
- Reproducibility: pin the tested optional package version; keep weights out of Git.
- Explicit exception: the owner requested committing and pushing these two consented reference clips. Generated previews remain local.

## Project Structure

```text
content-studio/skills/content-studio-video/audio/voice-cloning/
  scripts/voice.py
  scripts/chatterbox_backend.py
  profiles/en-raghu/
  tests/test_voice.py
  tests/test_chatterbox_backend.py
  SKILL.md
  README.md
  methods.json
  references/chatterbox-turbo.md
```

**Structure Decision**: Extend the canonical voice-cloning leaf. Keep the backend optional and load it only for an English profile.

## Design

- `profile.json` declares `backend.name=ChatterboxTurbo` and `references.take2/take3`, each with a SHA-256.
- `voice.py synthesize --reference-variant take2|take3` selects a bundled reference. The existing `--reference` and `--reference-text` remain for IndicF5.
- `chatterbox_backend.py` validates a local checkpoint directory, loads the model, and returns mono audio at its native sample rate.
- The narration manifest binds backend, model revision, selected variant, source hash, text hash, seed, and timing so resume cannot reuse another take's output.
- The preview review is evidence for profile selection only. Each new script still needs word and listening review before production use.

## Verification

Run focused voice tests, `npm run check:docs`, `npm run check:capabilities`, and one real `voice.py synthesize` call with the local Chatterbox checkpoint. Probe and transcribe that exact WAV. Review staged files, then commit and push `main`.
