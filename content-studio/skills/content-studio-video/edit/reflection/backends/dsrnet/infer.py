"""DSRNet inference adapter.

The network in ``model.py`` and ``lrm.py`` is vendored from XReflection
(https://github.com/hainuo-wang/XReflection, Apache-2.0). See ``NOTICE.md``.
Checkpoints are not bundled: this adapter downloads the released weights on
request and records their SHA-256 in the evidence report.

DSRNet predicts a transmission layer, a reflection layer, and a residual such
that ``clean + reflection + residual ~= input``. It was trained on 224 px
crops of synthetic and real pairs, so a full 1080p frame is resized to a
multiple-of-32 working width before inference. The caller decides how to put
the low-resolution prediction back onto the native frame; see
``detail_preserving_fuse`` in ``scripts/ai.py``.
"""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .geometry import SIZE_MULTIPLE, working_size
from .model import DSRNet

CHECKPOINT_URL = "https://checkpoints.mingjia.li/dsr-25.8915.ckpt"
CHECKPOINT_BYTES = 1_657_092_053
CHECKPOINT_SHA256 = "337e23a63fd93fc154330a6bbe21894ebd030fe9b8fa68ea7a6c8173e90f83aa"
ARCH = {
    "in_channels": 3,
    "out_channels": 3,
    "width": 64,
    "middle_blk_num": 12,
    "enc_blk_nums": [2, 2, 4, 8],
    "dec_blk_nums": [2, 2, 2, 2],
    "lrm_blk_nums": [2, 4],
}
VGG_INDICES = [2, 7, 12, 21, 30]


def default_weights_path() -> Path:
    """Return the per-user cache path used by the content-studio skills."""
    override = os.environ.get("CONTENT_STUDIO_REFLECTION_WEIGHTS")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return root / "content-studio" / "models" / "dsr-25.8915.ckpt"


def checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_checkpoint(destination: Path | None = None) -> Path:
    """Download the released DSRNet checkpoint and verify its digest."""
    target = destination or default_weights_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    print(f"downloading DSRNet checkpoint -> {target}", file=sys.stderr)
    with urllib.request.urlopen(CHECKPOINT_URL) as response, temporary.open("wb") as handle:
        total = int(response.headers.get("Content-Length") or CHECKPOINT_BYTES)
        copied = 0
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            handle.write(block)
            copied += len(block)
            if copied % (64 * 1024 * 1024) < 1024 * 1024:
                print(f"  {copied / 1e9:.2f} / {total / 1e9:.2f} GB", file=sys.stderr)
    digest = checkpoint_sha256(temporary)
    if digest.lower() != CHECKPOINT_SHA256:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"checkpoint digest mismatch: {digest}")
    temporary.replace(target)
    return target


class DSRNetBackend:
    """Load DSRNet once and decompose RGB frames (float32, 0-1, HxWx3)."""

    def __init__(self, weights: Path | None = None, device: str | None = None,
                 half: bool = True) -> None:
        self.weights = Path(weights) if weights else default_weights_path()
        if not self.weights.is_file():
            raise FileNotFoundError(
                f"DSRNet checkpoint not found: {self.weights}\n"
                "Download it with --download or set CONTENT_STUDIO_REFLECTION_WEIGHTS.")
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.half = bool(half and device == "cuda")
        self.model = self._load_model()
        self.vgg = self._load_vgg()
        self.peak_memory_mb = 0.0

    def _load_model(self) -> DSRNet:
        model = DSRNet(**ARCH)
        checkpoint = torch.load(self.weights, map_location="cpu", weights_only=False)
        state = checkpoint.get("state_dict", checkpoint)
        state = {key[len("net_g."):]: value for key, value in state.items()
                 if key.startswith("net_g.")}
        if not state:
            raise RuntimeError("checkpoint has no net_g state_dict entries")
        model.load_state_dict(state, strict=True)
        model.eval().requires_grad_(False)
        return model.to(self.device)

    def _load_vgg(self) -> torch.nn.Module:
        from torchvision.models import VGG19_Weights, vgg19

        features = vgg19(weights=VGG19_Weights.IMAGENET1K_V1).features.eval()
        for parameter in features.parameters():
            parameter.requires_grad_(False)
        return features.to(self.device)

    def _features(self, tensor: torch.Tensor) -> list[torch.Tensor]:
        outputs, current = [], tensor
        for index, layer in enumerate(self.vgg):
            current = layer(current)
            if index + 1 in VGG_INDICES:
                outputs.append(current)
            if index + 1 == VGG_INDICES[-1]:
                break
        return outputs

    def decompose(self, rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return ``(clean, reflection, residual)`` for one RGB frame.

        The frame must already be sized to a multiple of 32.
        """
        height, width, channels = rgb.shape
        if channels != 3:
            raise ValueError("expected HxWx3 RGB")
        if height % SIZE_MULTIPLE or width % SIZE_MULTIPLE:
            raise ValueError(f"frame must be a multiple of {SIZE_MULTIPLE}: {width}x{height}")

        tensor = torch.from_numpy(np.ascontiguousarray(rgb, dtype=np.float32))
        tensor = tensor.permute(2, 0, 1).unsqueeze(0).to(self.device)
        if self.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():
            with torch.autocast("cuda", dtype=torch.float16, enabled=self.half):
                clean, reflection, residual = self.model(tensor, self._features(tensor))
        if self.device == "cuda":
            self.peak_memory_mb = max(self.peak_memory_mb,
                                      torch.cuda.max_memory_allocated() / 1e6)
        return tuple(item[0].float().permute(1, 2, 0).cpu().numpy()
                     for item in (clean, reflection, residual))

    def resize(self, rgb: np.ndarray, width: int, height: int) -> np.ndarray:
        tensor = torch.from_numpy(np.ascontiguousarray(rgb, dtype=np.float32))
        tensor = tensor.permute(2, 0, 1).unsqueeze(0)
        tensor = F.interpolate(tensor, size=(height, width), mode="bicubic",
                               align_corners=False, antialias=True)
        return tensor[0].clamp(0, 1).permute(1, 2, 0).cpu().numpy()

    def reflect(self, rgb: np.ndarray, max_width: int = 640) -> dict:
        """Run DSRNet on a resized copy and return every useful layer.

        ``clean_low`` and ``input_low`` are both upscaled back to the native
        frame size with the same bicubic filter so their difference isolates the
        model's low-frequency correction.
        """
        height, width, _ = rgb.shape
        work_width, work_height = working_size(width, height, max_width)
        small = self.resize(rgb, work_width, work_height)
        clean, reflection, residual = self.decompose(small)
        return {
            "work_size": [work_width, work_height],
            "small": small,
            "clean": np.clip(clean, 0.0, 1.0),
            "reflection": reflection,
            "residual": residual,
            "clean_low": self.resize(np.clip(clean, 0.0, 1.0), width, height),
            "input_low": self.resize(small, width, height),
        }

    def close(self) -> None:
        self.model = None
        self.vgg = None
        if self.device == "cuda":
            torch.cuda.empty_cache()
