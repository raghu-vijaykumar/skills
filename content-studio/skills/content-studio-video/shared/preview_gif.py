"""Build labelled, time-aligned GIF evidence from bounded video outputs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, ImageOps


FrameTransform = Callable[[Image.Image], Image.Image]


def _frames(path: Path, start: float, duration: float, fps: int,
            decode_size: tuple[int, int] | None) -> list[Image.Image]:
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    stream = json.loads(info.stdout)["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    if decode_size:
        width, height = decode_size
    filters = f"fps={fps}"
    if decode_size:
        filters += f",scale={width}:{height}:flags=lanczos"
    decoded = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
         "-ss", str(start), "-i", str(path), "-t", str(duration),
         "-vf", filters, "-an", "-pix_fmt", "rgb24",
         "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    )
    stride = width * height * 3
    if len(decoded.stdout) % stride:
        raise ValueError(f"Incomplete decoded frame from {path}")
    return [Image.frombytes("RGB", (width, height), decoded.stdout[i:i + stride])
            for i in range(0, len(decoded.stdout), stride)]


def write_comparison(
    videos: list[Path], labels: list[str], output: Path, *, start: float = 0,
    duration: float = 1.5, fps: int = 8, panel: tuple[int, int] = (320, 180),
    transforms: list[FrameTransform] | None = None,
    starts: list[float] | None = None,
    decode_size: tuple[int, int] | None = None,
) -> int:
    """Show the same bounded time window in each panel; return GIF frame count."""
    if len(videos) < 2 or len(videos) != len(labels):
        raise ValueError("Comparison needs matching video and label lists")
    if transforms is not None and len(transforms) != len(videos):
        raise ValueError("Provide one transform per video")
    if starts is not None and len(starts) != len(videos):
        raise ValueError("Provide one source start per video")
    starts = starts or [start] * len(videos)
    sequences = [_frames(Path(path), offset, duration, fps, decode_size)
                 for path, offset in zip(videos, starts)]
    count = min(map(len, sequences))
    if count < 2:
        raise ValueError("Comparison needs at least two time-aligned frames")
    width, height = panel
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = (ImageFont.truetype(str(font_path), 16) if font_path.is_file()
            else ImageFont.load_default())
    result = []
    for index in range(count):
        card = Image.new("RGB", (width * len(videos), height + 28), "#111820")
        draw = ImageDraw.Draw(card)
        for column, (sequence, label) in enumerate(zip(sequences, labels)):
            frame = sequence[index]
            frame = (transforms[column](frame) if transforms else
                     ImageOps.fit(frame, panel, method=Image.Resampling.LANCZOS))
            if frame.size != panel:
                raise ValueError(f"Panel transform did not produce {panel}")
            card.paste(frame, (column * width, 28))
            draw.text((column * width + 8, 5), label, font=font, fill="white")
        # Quantize each complete card so labels and scene colors share a palette.
        result.append(card.quantize(colors=128, method=Image.Quantize.FASTOCTREE))
    output.parent.mkdir(parents=True, exist_ok=True)
    result[0].save(output, save_all=True, append_images=result[1:],
                   duration=round(1000 / fps), loop=0, optimize=True, disposal=2)
    return count
