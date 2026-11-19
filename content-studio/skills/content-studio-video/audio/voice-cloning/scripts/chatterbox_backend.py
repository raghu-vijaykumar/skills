#!/usr/bin/env python3
"""Optional local Chatterbox Turbo backend for consented English narration."""

from __future__ import annotations

from pathlib import Path


REQUIRED_MODEL_FILES = (
    "t3_turbo_v1.safetensors",
    "s3gen_meanflow.safetensors",
    "ve.safetensors",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.json",
    "merges.txt",
)


def validate_model_dir(model_dir: Path) -> Path:
    """Fail before loading Torch when a local checkpoint is incomplete."""
    root = Path(model_dir).expanduser().resolve()
    missing = [name for name in REQUIRED_MODEL_FILES if not (root / name).is_file()]
    if missing:
        raise SystemExit(
            "Chatterbox Turbo model directory is incomplete: " + ", ".join(missing)
        )
    return root


def load_backend(model_dir: Path, device: str):
    """Load weights only for a profile that explicitly requests this backend."""
    root = validate_model_dir(model_dir)
    try:
        from chatterbox.tts_turbo import ChatterboxTurboTTS
    except ImportError as error:
        raise SystemExit(
            "Chatterbox Turbo is optional; install chatterbox-tts==0.1.7 "
            "and setuptools<81 in an isolated Python 3.11 environment"
        ) from error
    return ChatterboxTurboTTS.from_local(root, device=device)


def synthesize(model, reference: Path, text: str, seed: int):
    """Return a finite mono waveform for the existing segment writer."""
    import numpy as np
    import torch

    torch.manual_seed(seed)
    # The approved comparison used the model's default delivery settings.
    rendered = model.generate(text, audio_prompt_path=str(reference))
    audio = rendered.detach().cpu().numpy()
    if audio.ndim == 2 and audio.shape[0] == 1:
        audio = audio[0]
    if audio.ndim != 1 or not audio.size or not np.isfinite(audio).all():
        raise ValueError("Chatterbox Turbo returned invalid mono audio")
    sample_rate = int(model.sr)
    if sample_rate <= 0:
        raise ValueError("Chatterbox Turbo returned an invalid sample rate")
    return audio.astype(np.float32, copy=False), sample_rate
