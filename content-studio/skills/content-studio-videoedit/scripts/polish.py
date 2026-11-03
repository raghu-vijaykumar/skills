#!/usr/bin/env python3
"""Ordered restoration polish: lens/perspective, denoise, deflicker, match, sharpen.

Order matters:
  lens geometry -> rolling-shutter/perspective -> temporal denoise -> deflicker
  -> shot matching -> sharpen -> encode

Upscaling is a separate stage and should run after denoise/deflicker and before
final sharpening and creative grading.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

import enhance

DENOISE = {
    "light": "hqdn3d=2:1:3:2",
    "medium": "hqdn3d=4:3:6:4",
    "nlmeans": "nlmeans=s=1.5:p=7:r=15",
}
SHARPEN = {
    "light": "cas=strength=0.25",
    "medium": "cas=strength=0.45",
    "strong": "unsharp=5:5:0.7:5:5:0.0",
}


class PolishError(RuntimeError):
    pass


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise PolishError((result.stderr or result.stdout)[-3000:])


def probe(path: Path) -> dict:
    return enhance.probe_video(path)


def mean_color(path: Path, duration: float) -> dict:
    samples = []
    for fraction in (0.2, 0.5, 0.8):
        rgb = enhance.extract_frame(path, max(0.0, duration * fraction))
        samples.append(rgb.reshape(-1, 3).mean(axis=0))
    return {"r": float(np.mean([s[0] for s in samples])),
            "g": float(np.mean([s[1] for s in samples])),
            "b": float(np.mean([s[2] for s in samples]))}


def match_gains(source: Path, reference: Path, duration: float) -> dict | None:
    src = mean_color(source, duration)
    ref = mean_color(reference, duration)
    target = (ref["r"] + ref["g"] + ref["b"]) / 3.0
    gains = {}
    for key in ("r", "g", "b"):
        # Preserve the reference's channel balance relative to its own average.
        desired = ref[key]
        current = max(src[key], 1e-4)
        gains[key] = round(max(0.85, min(1.15, desired / max(current, 1e-4))), 4)
    return gains


def build_filter(args, info: dict) -> tuple[list[str], dict]:
    filters = []
    used = {}
    if args.lens_k1 is not None or args.lens_k2 is not None:
        k1 = float(args.lens_k1 or 0.0)
        k2 = float(args.lens_k2 or 0.0)
        filters.append(f"lenscorrection=k1={k1}:k2={k2}:i=bilinear")
        used["lens"] = {"k1": k1, "k2": k2}
    if args.perspective:
        filters.append(f"perspective={args.perspective}")
        used["perspective"] = args.perspective
    if args.denoise != "off":
        filters.append(DENOISE[args.denoise])
        used["denoise"] = args.denoise
    if args.deflicker:
        filters.append("deflicker=mode=pm:size=10")
        used["deflicker"] = True
    if args.match_reference:
        reference = Path(args.match_reference).expanduser().resolve()
        if not reference.is_file():
            raise PolishError(f"match reference missing: {reference}")
        ref_info = probe(reference)
        gains = match_gains(Path(args.input), reference,
                            min(info["duration_seconds"], ref_info["duration_seconds"]))
        if gains:
            filters.append("colorchannelmixer="
                           f"rr={gains['r']}:gg={gains['g']}:bb={gains['b']}")
            used["match_reference"] = str(reference)
            used["match_gains"] = gains
    if args.sharpen != "off":
        filters.append(SHARPEN[args.sharpen])
        used["sharpen"] = args.sharpen
    return filters, used


def polish(args) -> dict:
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise PolishError(f"input missing: {source}")
    if source == output:
        raise PolishError("output must differ from the input")
    info = probe(source)
    if not info["has_audio"]:
        raise PolishError("audio is required; run audio mastering separately if needed")
    filters, used = build_filter(args, info)
    if not filters:
        raise PolishError("no filters selected")
    output.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(source), "-vf", ",".join(filters),
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
         str(output)])
    produced = probe(output)
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(source),
        "output": str(output),
        "filters": filters,
        "used": used,
        "source_size": [info["width"], info["height"]],
        "output_size": [produced["width"], produced["height"]],
        "duration_seconds": round(produced["duration_seconds"], 3),
        "note": "audio is copied; audio cleanup is a separate stage",
    }
    (output.parent / "polish.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lens-k1", type=float)
    parser.add_argument("--lens-k2", type=float)
    parser.add_argument("--perspective", help="raw FFmpeg perspective coordinates")
    parser.add_argument("--denoise", choices=["off", "light", "medium", "nlmeans"],
                        default="light")
    parser.add_argument("--deflicker", action="store_true")
    parser.add_argument("--match-reference", type=Path,
                        help="match this clip's mean channel balance to a reference clip")
    parser.add_argument("--sharpen", choices=["off", "light", "medium", "strong"],
                        default="off",
                        help="run after upscaling for best results")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(polish(args), indent=2))
        return 0
    except (PolishError, OSError, ValueError) as exc:
        print(f"polish: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
