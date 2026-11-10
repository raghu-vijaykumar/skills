#!/usr/bin/env python3
"""IndicF5 loader and inference wrapper.

Heavy imports stay inside functions so enrollment and unit tests work without
Torch. The published IndicF5 ``model.py`` does not load the released weights, so
this module loads ``model.safetensors`` directly and verifies the tensor count.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

DEFAULT_NFE_STEP = 32
DEFAULT_CFG_STRENGTH = 2.0
EMA_PREFIX = "ema_model._orig_mod."
MODEL_CONFIG = {
    "dim": 1024,
    "depth": 22,
    "heads": 16,
    "ff_mult": 2,
    "text_dim": 512,
    "conv_layers": 4,
}
DROP_KEYS = {
    "mel_spec.mel_stft.mel_scale.fb",
    "mel_spec.mel_stft.spectrogram.window",
}


def validate_model_dir(model_dir: Path) -> tuple[Path, Path]:
    """Return the weights and vocabulary paths or fail with a usable message."""
    model_dir = Path(model_dir).expanduser().resolve()
    weights = model_dir / "model.safetensors"
    vocab = model_dir / "checkpoints" / "vocab.txt"
    if not weights.is_file():
        raise SystemExit(f"IndicF5 weights not found: {weights}")
    if not vocab.is_file():
        raise SystemExit(f"IndicF5 vocabulary not found: {vocab}")
    return weights, vocab


def _patch_torchaudio() -> None:
    """TorchAudio 2.11 needs TorchCodec; decode with SoundFile instead."""
    import soundfile
    import torch
    import torchaudio

    def load_with_soundfile(path, *args, **kwargs):
        data, sample_rate = soundfile.read(
            str(path), always_2d=True, dtype="float32"
        )
        return torch.from_numpy(data.T.copy()), sample_rate

    torchaudio.load = load_with_soundfile


def load_backend(
    model_dir: Path,
    device: str = "cuda",
    allow_partial_weights: bool = False,
):
    """Build the CFM model, load the released EMA weights, and load the vocoder."""
    weights_path, vocab_path = validate_model_dir(model_dir)
    _patch_torchaudio()

    from f5_tts.infer import utils_infer
    from f5_tts.model import CFM, DiT
    from safetensors.torch import load_file
    import torch

    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA is unavailable; falling back to CPU", flush=True)
        device = "cpu"

    # Recent F5-TTS requires a checkpoint path in load_model(), which would
    # process IndicF5's EMA keys incorrectly before our verified loader runs.
    # Construct the same CFM graph directly, then load only the released EMA.
    vocab_map, vocab_size = utils_infer.get_tokenizer(str(vocab_path), "custom")
    model = CFM(
        transformer=DiT(**MODEL_CONFIG, text_num_embeds=vocab_size,
                        mel_dim=utils_infer.n_mel_channels),
        mel_spec_kwargs={
            "n_fft": utils_infer.n_fft,
            "hop_length": utils_infer.hop_length,
            "win_length": utils_infer.win_length,
            "n_mel_channels": utils_infer.n_mel_channels,
            "target_sample_rate": utils_infer.target_sample_rate,
            "mel_spec_type": "vocos",
        },
        odeint_kwargs={"method": utils_infer.ode_method},
        vocab_char_map=vocab_map,
    ).to(device)
    state = load_file(str(weights_path), device="cpu")
    tensors = {
        key[len(EMA_PREFIX) :]: value
        for key, value in state.items()
        if key.startswith(EMA_PREFIX)
    }
    for key in DROP_KEYS:
        tensors.pop(key, None)
    missing, unexpected = model.load_state_dict(tensors, strict=False)
    if (missing or unexpected) and not allow_partial_weights:
        raise SystemExit(
            "IndicF5 weights do not match the model: "
            f"{len(missing)} missing, {len(unexpected)} unexpected. "
            "Use --allow-partial-weights only for a reviewed fine-tune."
        )
    model.eval()
    local_vocoder = os.environ.get("CONTENT_STUDIO_VOCODER_DIR")
    vocoder = utils_infer.load_vocoder(
        vocoder_name="vocos", is_local=bool(local_vocoder),
        local_path=local_vocoder or "", device=device,
    )
    return model, vocoder


def prepare_reference(reference_audio: Path, reference_text: str):
    """Normalize the reference clip once and reuse it for every section."""
    _patch_torchaudio()
    from f5_tts.infer.utils_infer import preprocess_ref_audio_text

    return preprocess_ref_audio_text(
        str(reference_audio), reference_text, show_info=lambda *_: None
    )


def synthesize(
    model,
    vocoder,
    reference_audio,
    reference_text: str,
    text: str,
    nfe_step: int = DEFAULT_NFE_STEP,
    cfg_strength: float = DEFAULT_CFG_STRENGTH,
    speed: float = 1.0,
    device: str = "cuda",
    seed: int | None = None,
):
    """Generate one section and return a mono float32 array plus sample rate."""
    import numpy as np
    import torch
    from f5_tts.infer.utils_infer import infer_process

    if seed is not None:
        torch.manual_seed(seed)
    audio, sample_rate, _ = infer_process(
        reference_audio,
        reference_text,
        text,
        model,
        vocoder,
        mel_spec_type="vocos",
        speed=speed,
        nfe_step=nfe_step,
        cfg_strength=cfg_strength,
        device=device,
    )
    return np.asarray(audio, dtype=np.float32).reshape(-1), int(sample_rate)


def keep_system_awake() -> None:
    """Prevent idle sleep from suspending a long CUDA render on Windows."""
    if sys.platform != "win32":
        return
    import ctypes

    es_continuous = 0x80000000
    es_system_required = 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(
        es_continuous | es_system_required
    )
