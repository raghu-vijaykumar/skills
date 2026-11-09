"""Build small, reproducible transition GIFs from the skill's actual renderers.

The synthetic A/B cards make the direction and reveal of each effect easy to
inspect without placing private draft footage in the repository.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from transitions import load_catalog, render_join, render_point


SKILL = Path(__file__).resolve().parents[1]
PREVIEWS = SKILL / "previews"
SOURCE_SIZE = (320, 180)
FRAME_RATE = 12
CLIP_SECONDS = 1.25
JOIN_SECONDS = 0.7


def run(*command: str) -> None:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def card(path: Path, label: str) -> None:
    # Deliberately distinct geometry and colors expose direction, blur, and masks.
    a = label == "A"
    image = Image.new("RGB", SOURCE_SIZE, "#153f60" if a else "#8f3158")
    draw = ImageDraw.Draw(image)
    for x in range(0, 320, 32):
        draw.line((x, 0, x, 180), fill="#34627a" if a else "#a24c71", width=1)
    for y in range(0, 180, 30):
        draw.line((0, y, 320, y), fill="#34627a" if a else "#a24c71", width=1)
    if a:
        draw.rounded_rectangle((27, 30, 157, 150), radius=27, fill="#10c4b0")
        draw.ellipse((183, 45, 278, 140), fill="#f8c658")
    else:
        draw.polygon(((27, 140), (100, 28), (172, 140)), fill="#ffb756")
        draw.rounded_rectangle((192, 33, 284, 150), radius=12, fill="#f36689")
    draw.text((62, 50) if a else (69, 51), label, font=font(75), fill="white", stroke_width=1, stroke_fill="#18344e")
    draw.rectangle((0, 155, 320, 180), fill="#102d42" if a else "#61243f")
    draw.text((14, 158), "OUTGOING" if a else "INCOMING", font=font(14), fill="white")
    image.save(path)


def source_clip(still: Path, output: Path) -> None:
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-loop", "1", "-framerate", str(FRAME_RATE), "-i", str(still),
        "-t", str(CLIP_SECONDS), "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p", str(output))


def point_source(a: Path, b: Path, output: Path) -> None:
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(a), "-i", str(b), "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(output))


def gif(source: Path, output: Path, start: float, seconds: float) -> None:
    # A generated palette keeps previews legible while limiting repository size.
    graph = ("fps=10,scale=240:135:flags=lanczos,split[p][g];"
             "[p]palettegen=max_colors=64:stats_mode=diff[pal];"
             "[g][pal]paletteuse=dither=bayer:bayer_scale=3")
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", str(start), "-t", str(seconds), "-i", str(source),
        "-filter_complex", graph, "-loop", "0", str(output))


def build(output_dir: Path, only: set[str] | None = None) -> list[Path]:
    items = load_catalog()["transitions"]
    known = {item["id"] for item in items}
    if only and only - known:
        raise ValueError(f"Unknown transition IDs: {', '.join(sorted(only - known))}")
    output_dir.mkdir(parents=True, exist_ok=True)
    built: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="transition-gallery-") as temp:
        work = Path(temp)
        for label in ("A", "B"):
            card(work / f"{label}.png", label)
            source_clip(work / f"{label}.png", work / f"{label}.mp4")
        point_source(work / "A.mp4", work / "B.mp4", work / "point-master.mp4")
        for item in items:
            effect = item["id"]
            if only and effect not in only:
                continue
            rendered = work / f"{effect}.mp4"
            if "join" in item["modes"]:
                render_join({"inputs": [str(work / "A.mp4"), str(work / "B.mp4")],
                             "transitions": [{"after": 0, "id": effect,
                                              "duration": JOIN_SECONDS}]},
                            rendered, size=SOURCE_SIZE, fps=FRAME_RATE, audio="none")
                start, seconds = 0.0, 1.8
            else:
                render_point(work / "point-master.mp4", rendered,
                             {"transitions": [{"at": CLIP_SECONDS, "id": effect,
                                               "duration": item["default_duration"]}]})
                start, seconds = 0.35, 1.8
            output = output_dir / f"{effect}.gif"
            gif(rendered, output, start, seconds)
            built.append(output)
            print(f"{effect}: {output.stat().st_size // 1024} KiB", flush=True)
    return built


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PREVIEWS)
    parser.add_argument("--only", nargs="*", help="Optional transition IDs to rebuild")
    args = parser.parse_args()
    built = build(args.output_dir, set(args.only) if args.only else None)
    print(f"Built {len(built)} GIFs ({sum(p.stat().st_size for p in built) // 1024} KiB total)")


if __name__ == "__main__":
    main()
