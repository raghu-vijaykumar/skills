#!/usr/bin/env python3
"""Build silent, time-aligned GIF evidence from a reviewed real clipping master."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SKILL = Path(__file__).resolve().parents[1]
VIDEO = SKILL.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(VIDEO / "shared"))
import clipping  # noqa: E402
from preview_gif import _frames  # noqa: E402


def _font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), 16) if path.is_file() else ImageFont.load_default()


def _card(source: Image.Image, reel: Image.Image, crop: dict,
          source_time: float) -> Image.Image:
    card = Image.new("RGB", (640, 348), "#111820")
    card.paste(source, (0, 98))
    card.paste(reel, (390, 28))
    draw = ImageDraw.Draw(card)
    draw.text((8, 5), f"SOURCE  {int(source_time // 60):02d}:{source_time % 60:04.1f}",
              font=_font(), fill="white")
    draw.text((390, 5), "REVIEWED 9:16 CLIP", font=_font(), fill="white")
    draw.rectangle((round(crop["x"] * 320), round(98 + crop["y"] * 180),
                    round((crop["x"] + crop["w"]) * 320),
                    round(98 + (crop["y"] + crop["h"]) * 180)),
                   outline="#fff2b1", width=3)
    return card


def build(source: Path, render: Path, selection: Path, output: Path,
          *, preview: bool = False) -> dict:
    """Check the current source binding, then compare the exact rendered bytes."""
    source, render, selection, output = (source.resolve(), render.resolve(),
                                          selection.resolve(), output.resolve())
    checked = clipping.validate_selection(selection, source_override=source, ready=True)
    if not render.is_file():
        raise ValueError("The exact delivered master is missing")
    if not preview:
        # README evidence must bind to the approved full render, never a bounded preview.
        record_path = render.with_suffix(render.suffix + ".render.json")
        if not record_path.is_file():
            raise ValueError("Approved full-render record is missing")
        delivery = json.loads(record_path.read_text(encoding="utf-8-sig"))
        if (delivery.get("output") != str(render)
                or delivery.get("output_sha256") != clipping.sha256_file(render)
                or not delivery.get("approval_fingerprint")
                or delivery.get("video_encoder_invocations") != 1
                or delivery.get("audio_encoder_invocations") != 1):
            raise ValueError("Full-render record does not match the delivered master")
    record = json.loads(selection.read_text(encoding="utf-8-sig"))
    beginning, end = checked["selected"]
    duration = end - beginning
    info = clipping.media_info(render)
    if (not info["video"] or not info["audio"]
            or (info["video"]["width"], info["video"]["height"]) != (360, 640)
            or abs(info["duration"] - duration) > .12):
        raise ValueError("Delivered video, audio, dimensions, or duration differ from the plan")
    source_frames = _frames(source, beginning, duration, 6, (320, 180))
    reel_frames = _frames(render, 0, duration, 6, (180, 320))
    count = min(len(source_frames), len(reel_frames))
    if count < 3:
        raise ValueError("Comparison needs at least three time-aligned frames")
    cards = []
    for index in range(count):
        at = beginning + index / 6
        crop = next((item for item in checked["crop_intervals"]
                     if item["source_in"] <= at < item["source_out"]), None)
        if crop is None:
            raise ValueError("No crop interval covers a comparison frame")
        cards.append(_card(source_frames[index], reel_frames[index], crop, at)
                     .quantize(colors=128, method=Image.Quantize.FASTOCTREE))
    output.mkdir(parents=True, exist_ok=True)
    comparison = output / "real-source-vs-reel.gif"
    cards[0].save(comparison, save_all=True, append_images=cards[1:],
                  duration=167, loop=0, optimize=True, disposal=2)
    clipped_frames = _frames(render, 0, duration, 8, (180, 320))
    if len(clipped_frames) < 3:
        raise ValueError("Clipped GIF needs at least three frames")
    palette = [frame.quantize(colors=128, method=Image.Quantize.FASTOCTREE)
               for frame in clipped_frames]
    clipped = output / "real-clipped-reel.gif"
    palette[0].save(clipped, save_all=True, append_images=palette[1:],
                    duration=125, loop=0, optimize=True, disposal=2)
    return {"source": str(source), "source_sha256": checked["source_sha256"],
            "render": str(render), "selection": str(selection),
            "source_range": [beginning, end], "crop_intervals": len(checked["crop_intervals"]),
            "framing_report": record["crop_intervals"][0]["framing_file"],
            "comparison_frames": count, "clipped_frames": len(palette),
            "comparison_bytes": comparison.stat().st_size,
            "clipped_bytes": clipped.stat().st_size}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true",
                        help="Generate temporary review GIFs without a final-render record")
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.source, arguments.render,
                           arguments.selection, arguments.output,
                           preview=arguments.preview), indent=2))
