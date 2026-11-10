"""Render bounded restoration examples from an approved, published SDR video.

The original media stays outside Git. Reproducible defects are introduced only
in temporary clips, then the owning specialist scripts render the corrections.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts"
sys.path.insert(0, str(SKILL.parent.parent / "shared"))
from preview_gif import write_comparison  # noqa: E402


def run(command: list[str]) -> bytes:
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1800:].decode("utf-8", "replace"))
    return result.stdout


def encode(source: Path, target: Path, filters: str, start: float | None = None) -> None:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    if start is not None:
        command += ["-ss", str(start)]
    # The specialist polish route requires an audio stream. Use silence rather
    # than carrying music or speech from the published example into the repo.
    command += ["-i", str(source), "-f", "lavfi", "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map", "0:v:0", "-map", "1:a:0", "-t", "2.5", "-vf", filters,
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", str(target)]
    run(command)


def render(method: str, source: Path, target: Path, *options: str) -> None:
    run(["python", str(SCRIPT / f"{method.replace('-', '_')}.py"),
         "--input", str(source), "--output", str(target), *options])


def build(source: Path, at: float, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="restoration-gallery-") as directory:
        work = Path(directory)
        natural = work / "natural.mp4"
        encode(source, natural, "scale=640:360:flags=lanczos,fps=12", start=at)
        inputs = {
            "noisy": "noise=alls=22:allf=t+u",
            "flicker": "eq=brightness='0.11*sin(2*PI*n/6)'",
            "blurred": "gblur=sigma=1.6",
            "distorted": "drawgrid=w=80:h=80:t=1:c=white@0.5,"
                         "lenscorrection=k1=-0.18:k2=0.04:i=bilinear",
        }
        for name, filters in inputs.items():
            encode(natural, work / f"{name}.mp4", filters)
        recipes = (
            ("denoise-light", "noisy", (), True),
            ("denoise-medium", "noisy", (), True),
            ("denoise-nlmeans", "noisy", (), True),
            ("deflicker", "flicker", (), False),
            ("lens", "distorted", ("--lens-k1", "0.18", "--lens-k2", "-0.04"), False),
            ("sharpen-light", "blurred", (), True),
            ("sharpen-medium", "blurred", (), True),
        )
        for method, input_name, options, crop in recipes:
            before = work / f"{input_name}.mp4"
            after = work / f"{method}.mp4"
            render(method, before, after, *options)
            target = output / f"{method}.gif"
            # Moving panels expose temporal damage that a still cannot show.
            transforms = ([lambda image: image.crop((200, 70, 520, 250))] * 2
                          if crop else None)
            write_comparison([before, after], ["BEFORE", f"AFTER: {method}"],
                             target, duration=2.5, fps=8, transforms=transforms)
            print(f"{method}: {target.stat().st_size // 1024} KiB", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--at", type=float, default=245.0)
    parser.add_argument("--output", type=Path, default=SKILL / "previews")
    args = parser.parse_args()
    build(args.source_video, args.at, args.output)


if __name__ == "__main__":
    main()
