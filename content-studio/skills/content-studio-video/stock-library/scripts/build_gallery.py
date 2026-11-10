"""Make small catalogue GIFs from reviewed CTA assets and public footage.

The source footage and full-resolution alpha movies stay outside this repo.
Each GIF is composited from the exact exported CTA clip, so it shows the
delivered motion rather than a drawing-only mock-up.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
VARIANTS = ("classic-bar", "minimal-pills", "bold-stack")


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1800:])


def reviewed_assets(library: Path) -> dict[str, Path]:
    entries = json.loads((library / "catalogue.json").read_text(encoding="utf-8"))["assets"]
    result = {}
    for variant in VARIANTS:
        name = variant.replace("-", " ")
        matches = [item for item in entries if item["kind"] == "cta"
                   and name in item["name"].lower() and item["rights"] == "owned"]
        if len(matches) != 1:
            raise ValueError(f"Expected one owned {variant} CTA in {library}")
        path = (library / matches[0]["relative_path"]).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        result[variant] = path
    return result


def build(library: Path, background_video: Path, at: float, output: Path) -> None:
    assets = reviewed_assets(library)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cta-gallery-") as directory:
        background = Path(directory) / "background.png"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
             "-ss", str(at), "-i", str(background_video), "-map", "0:v:0",
             "-frames:v", "1", "-vf", "scale=1280:720:flags=lanczos",
             str(background)])
        for variant, asset in assets.items():
            target = output / f"{variant}.gif"
            # Overlay the exported alpha movie on one real-world frame. Keeping
            # the background still makes the animation readable and compact.
            graph = ("[0:v]format=yuv420p[bg];"
                     "[1:v]scale=1280:720:flags=lanczos,format=yuva444p10le[cta];"
                     "[bg][cta]overlay=shortest=1:format=auto,"
                     "scale=480:270:flags=lanczos,fps=8,split[a][b];"
                     "[a]palettegen=max_colors=80:stats_mode=diff[pal];"
                     "[b][pal]paletteuse=dither=bayer:bayer_scale=3")
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                 "-loop", "1", "-framerate", "8", "-i", str(background),
                 "-i", str(asset), "-filter_complex", graph, "-t", "5",
                 "-loop", "0", str(target)])
            print(f"{variant}: {target.stat().st_size // 1024} KiB", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--background-video", type=Path, required=True)
    parser.add_argument("--at", type=float, default=95.0)
    parser.add_argument("--output", type=Path, default=SKILL / "previews")
    args = parser.parse_args()
    build(args.library, args.background_video, args.at, args.output)


if __name__ == "__main__":
    main()
