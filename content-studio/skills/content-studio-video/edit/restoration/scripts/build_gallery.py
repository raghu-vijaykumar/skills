"""Render bounded restoration examples from an approved, published SDR video.

The original media stays outside Git. Reproducible defects are introduced only
in temporary clips, then the owning specialist scripts render the corrections.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts"


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


def frame(source: Path, at: float = 1.2) -> Image.Image:
    data = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-ss", str(at), "-i", str(source), "-frames:v", "1",
                "-f", "image2pipe", "-vcodec", "png", "-"])
    return Image.open(io.BytesIO(data)).convert("RGB")


def pair(before: Path, after: Path, output: Path, crop: bool = True) -> None:
    images = [frame(before), frame(after)]
    if crop:
        images = [image.crop((200, 70, 520, 250)) for image in images]
    else:
        images = [image.resize((320, 180), Image.Resampling.LANCZOS) for image in images]
    result = Image.new("RGB", (640, 205), "#142838")
    draw = ImageDraw.Draw(result)
    for index, image in enumerate(images):
        result.paste(image, (index * 320, 0))
        draw.text((index * 320 + 8, 184), "BEFORE" if index == 0 else "AFTER",
                  fill="white", font=ImageFont.load_default())
    result.save(output, optimize=True)


def motion_pair(before: Path, after: Path, output: Path) -> None:
    # Only temporal defects need a GIF; both panels use the same source times.
    graph = ("[0:v]scale=320:180:flags=lanczos[a];"
             "[1:v]scale=320:180:flags=lanczos[b];"
             "[a][b]hstack=inputs=2,scale=480:135:flags=lanczos,fps=8,split[p][g];"
             "[p]palettegen=max_colors=72:stats_mode=diff[pal];"
             "[g][pal]paletteuse=dither=bayer:bayer_scale=3")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-i", str(before), "-i", str(after), "-filter_complex", graph,
         "-t", "2.5", "-loop", "0", str(output)])


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
            target = output / f"{method}{'.gif' if method == 'deflicker' else '.png'}"
            if method == "deflicker":
                motion_pair(before, after, target)
            else:
                pair(before, after, target, crop=crop)
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
