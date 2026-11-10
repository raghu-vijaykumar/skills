#!/usr/bin/env python3
"""Draw an original, reusable UHD CTA as transparent ProRes 4444 video."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


POSITIONS = {"top-right", "top-left", "bottom-right", "bottom-left", "center"}
VARIANTS = {
    "classic-bar": "Cream connected bar with sequential color changes (original design)",
    "minimal-pills": "Three separate translucent dark pills with bright active states",
    "bold-stack": "Compact vertical cards with a prominent subscribe action",
}


def smooth(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def states(t: float) -> dict[str, float | bool]:
    """Keep the visual beat sequence stable across frame rates and dimensions."""
    return {
        "entrance": smooth(t / 0.4),
        "like": t >= 0.65,
        "share": t >= 1.35,
        "subscribed": t >= 2.25,
        "bell": t >= 3.25,
        "exit": 1.0 - smooth((t - 4.45) / 0.55),
    }


@lru_cache(maxsize=16)
def font(size: int) -> ImageFont.FreeTypeFont:
    paths = [Path("C:/Windows/Fonts/arialbd.ttf"),
             Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]
    for path in paths:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("A bold Arial or DejaVu Sans font is required")


def box_position(width: int, height: int, box_width: int, box_height: int,
                 position: str) -> tuple[int, int]:
    margin = round(width * 0.035)
    top = round(height * 0.075)
    if position == "center":
        return ((width - box_width) // 2, (height - box_height) // 2)
    x = margin if position.endswith("left") else width - margin - box_width
    y = top if position.startswith("top") else height - top - box_height
    return x, y


def _draw_bell_badge(d: ImageDraw.ImageDraw, u, x: int, y: int, t: float) -> None:
    """The bell is a readable, gently ringing icon rather than a state dot."""
    swing = round(4 * math.sin(19 * t))
    x += swing
    d.ellipse((u(x), u(y), u(x + 64), u(y + 64)), fill="#F9CD63")
    d.arc((u(x + 20), u(y + 13), u(x + 44), u(y + 41)), 180, 360,
          fill="#173943", width=max(2, u(5)))
    d.polygon(((u(x + 18), u(y + 42)), (u(x + 46), u(y + 42)),
               (u(x + 51), u(y + 49)), (u(x + 13), u(y + 49))),
              fill="#173943")
    d.ellipse((u(x + 29), u(y + 50), u(x + 36), u(y + 57)), fill="#173943")


def draw_frame(t: float, width: int, height: int, duration: float,
               position: str, variant: str = "classic-bar") -> Image.Image:
    if position not in POSITIONS or variant not in VARIANTS or min(width, height) < 720 or duration < 4.8:
        raise ValueError("CTA needs a supported position, at least 720p, and 4.8 seconds")
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    scale = width / 3840
    # A variant owns its silhouette; the transparent canvas keeps all placements reusable.
    design_sizes = {"classic-bar": (1770, 232), "minimal-pills": (1710, 230),
                    "bold-stack": (790, 640)}
    bw, bh = (round(n * scale) for n in design_sizes[variant])
    x, y = box_position(width, height, bw, bh, position)
    state = states(t * 5.0 / duration)
    opacity = min(float(state["entrance"]), float(state["exit"]))
    if opacity <= 0:
        return canvas
    # The off-canvas travel is built into the transparent frame, making placement reusable.
    y -= round((1 - float(state["entrance"])) * 100 * scale)
    layer = Image.new("RGBA", (bw + 30, bh + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    u = lambda n: round(n * scale)
    if variant == "minimal-pills":
        # Separate chips leave the picture visible and read clearly on light or dark shots.
        chips = ((0, 430, "LIKE", "like", "#29B4D4"),
                 (455, 940, "SHARE", "share", "#34C2A0"),
                 (965, 1710, "SUBSCRIBED" if state["subscribed"] else "SUBSCRIBE",
                  "subscribed", "#FF6579"))
        for left, right, label, key, accent in chips:
            active = bool(state[key])
            fill = accent if active else (16, 38, 46, 226)
            d.rounded_rectangle((u(left), u(22), u(right), u(206)), radius=u(84),
                                fill=fill, outline=(255, 255, 255, 225), width=max(1, u(4)))
            size = 65 if len(label) < 10 else 55
            f = font(max(10, u(size)))
            bbox = d.textbbox((0, 0), label, font=f)
            tx = (u(left + right) - (bbox[2] - bbox[0])) / 2
            d.text((tx, u(112) - (bbox[3] - bbox[1]) / 2 - bbox[1]), label,
                   font=f, fill="#10262E" if active else "#FFFFFF")
        if state["bell"]:
            _draw_bell_badge(d, u, 1642, 0, t)
    elif variant == "bold-stack":
        # Vertical cards use less horizontal shot space and emphasize the final action.
        rows = ((0, "LIKE", "like", "#35B9DA"),
                (205, "SHARE", "share", "#42CAA9"),
                (410, "SUBSCRIBED" if state["subscribed"] else "SUBSCRIBE",
                 "subscribed", "#F36B7B"))
        for top, label, key, accent in rows:
            active = bool(state[key])
            fill = accent if active else (17, 44, 53, 235)
            d.rounded_rectangle((u(0), u(top), u(790), u(top + 184)),
                                radius=u(35), fill=fill,
                                outline=(255, 255, 255, 235), width=max(1, u(4)))
            d.ellipse((u(35), u(top + 39), u(145), u(top + 149)),
                      fill="#FFFFFF" if active else (75, 105, 112, 255))
            f = font(max(10, u(75 if len(label) < 10 else 62)))
            d.text((u(177), u(top + 47)), label, font=f,
                   fill="#102C35" if active else "#FFFFFF")
        if state["bell"]:
            _draw_bell_badge(d, u, 700, 412, t)
    else:
        _draw_classic_bar(d, state, t, u, bw, bh)
    if opacity < 1:
        layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
    canvas.alpha_composite(layer, (x, y))
    return canvas


def _draw_classic_bar(d: ImageDraw.ImageDraw, state: dict[str, float | bool],
                      t: float, u, bw: int, bh: int) -> None:
    """Preserve the approved original CTA artwork for existing callers."""
    navy, cream, coral, teal, blue, gold = (
        "#193D43", "#FFF8EB", "#EB5365", "#176F73", "#249AC2", "#E8AB37")
    d.rounded_rectangle((u(12), u(16), bw + u(11), bh + u(12)), radius=u(66), fill=(12, 31, 35, 120))
    d.rounded_rectangle((0, 0, bw, bh), radius=u(64), fill=cream, outline="#D8D5C9", width=max(1, u(3)))
    # Each control is legible by shape and label, with a modest animated state change.
    like_color = blue if state["like"] else navy
    thumb = [(u(95),u(116)),(u(132),u(116)),(u(151),u(80)),(u(167),u(72)),
             (u(180),u(78)),(u(177),u(113)),(u(207),u(114)),(u(215),u(126)),
             (u(197),u(177)),(u(120),u(177)),(u(95),u(159))]
    d.polygon(thumb, fill=like_color)
    d.rounded_rectangle((u(73),u(116),u(103),u(178)),radius=u(8),fill=like_color)
    d.text((u(241),u(82)), "LIKE", font=font(u(75)), fill=like_color)
    d.line((u(484),u(46),u(484),u(185)),fill="#D8D5C9",width=max(1,u(3)))
    share_color = teal if state["share"] else navy
    d.line((u(548),u(145),u(635),u(81),u(705),u(81)),fill=share_color,width=u(13),joint="curve")
    d.polygon([(u(706),u(81)),(u(672),u(52)),(u(672),u(110))],fill=share_color)
    d.text((u(731),u(82)), "SHARE", font=font(u(72)), fill=share_color)
    d.line((u(1045),u(46),u(1045),u(185)),fill="#D8D5C9",width=max(1,u(3)))
    subscribed = bool(state["subscribed"])
    button_color = navy if subscribed else coral
    d.rounded_rectangle((u(1092),u(36),u(1538),u(194)),radius=u(45),fill=button_color)
    label = "SUBSCRIBED" if subscribed else "SUBSCRIBE"
    label_font = font(u(59 if subscribed else 65))
    text_box = d.textbbox((0,0),label,font=label_font)
    d.text((u(1315)-(text_box[2]-text_box[0])/2,u(116)-(text_box[3]-text_box[1])/2-text_box[1]),
           label,font=label_font,fill="white")
    bell_color = gold if state["bell"] else navy
    d.arc((u(1589),u(63),u(1683),u(169)),180,360,fill=bell_color,width=u(12))
    d.polygon([(u(1586),u(143)),(u(1686),u(143)),(u(1702),u(165)),(u(1570),u(165))],fill=bell_color)
    d.ellipse((u(1621),u(170),u(1651),u(195)),fill=bell_color)
    if state["bell"]:
        phase = math.sin(20 * t)
        spread = u(15 + 4 * phase)
        d.arc((u(1555)-spread,u(49)-spread,u(1717)+spread,u(173)+spread),
              290,340,fill=bell_color,width=u(7))
        d.arc((u(1555)-spread,u(49)-spread,u(1717)+spread,u(173)+spread),
              200,250,fill=bell_color,width=u(7))


def probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=width,height,pix_fmt,avg_frame_rate,codec_name",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["streams"][0]


def render(output: Path, width: int, height: int, fps: int, duration: float,
           position: str, variant: str = "classic-bar") -> dict:
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    if output.suffix.lower() != ".mov" or fps not in {24, 25, 30, 50, 60}:
        raise ValueError("Output must be a new .mov at a supported frame rate")
    if width < 1280 or height < 720 or duration < 4.8 or position not in POSITIONS or variant not in VARIANTS:
        raise ValueError("Invalid CTA dimensions, duration, or position")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.stem + ".partial.mov")
    if partial.exists():
        raise ValueError(f"Partial output already exists: {partial}")
    count = round(fps * duration)
    command = ["ffmpeg", "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
               "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an",
               "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
               "-alpha_bits", "16", "-frames:v", str(count), str(partial)]
    try:
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE) as process:
            assert process.stdin is not None
            for index in range(count):
                frame = draw_frame(index / fps, width, height, duration, position, variant)
                process.stdin.write(frame.tobytes())
            process.stdin.close()
            error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            if process.wait() != 0:
                raise RuntimeError("CTA encode failed: " + error[-700:])
        video = probe(partial)
        if (video.get("width"), video.get("height")) != (width, height) or "a" not in video.get("pix_fmt", ""):
            raise RuntimeError(f"CTA alpha/dimensions not preserved: {video}")
        os.replace(partial, output)
        return video
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "render"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=int)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--position", choices=sorted(POSITIONS))
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="classic-bar")
    args = parser.parse_args()
    if args.command == "list":
        print(json.dumps(VARIANTS, indent=2))
        return
    if None in (args.output, args.width, args.height, args.fps, args.duration, args.position):
        parser.error("render requires --output, --width, --height, --fps, --duration, and --position")
    video = render(args.output, args.width, args.height, args.fps, args.duration,
                   args.position, args.variant)
    print(f"Rendered transparent CTA: {args.output} ({video['width']}x{video['height']}, {video['pix_fmt']})")


if __name__ == "__main__":
    main()
