#!/usr/bin/env python3
"""Measure SSIM, PSNR, and VMAF between a reference and a processed video."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


class QualityError(RuntimeError):
    pass


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise QualityError((result.stderr or result.stdout)[-3000:])
    return result.stderr or result.stdout


def measure(reference: Path, distorted: Path) -> dict:
    for path in (reference, distorted):
        if not path.is_file():
            raise QualityError(f"missing video: {path}")
    common = ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(reference),
              "-i", str(distorted)]
    ssim_log = run(common + ["-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"])
    psnr_log = run(common + ["-lavfi", "[0:v][1:v]psnr", "-f", "null", "-"])
    try:
        vmaf_log = run(common + ["-lavfi", "[0:v][1:v]libvmaf", "-f", "null", "-"])
        vmaf = re.search(r"VMAF score:\s*([0-9.]+)", vmaf_log)
    except QualityError:
        vmaf = None
    ssim = re.search(r"All:([0-9.]+)", ssim_log)
    psnr = re.search(r"average:([0-9.]+|inf)", psnr_log)
    psnr_value = None
    if psnr:
        psnr_value = float("inf") if psnr.group(1) == "inf" else float(psnr.group(1))
    return {
        "ssim": float(ssim.group(1)) if ssim else None,
        "psnr_db": psnr_value,
        "vmaf": float(vmaf.group(1)) if vmaf else None,
        "reference": str(reference.resolve()),
        "distorted": str(distorted.resolve()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--distorted", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = measure(args.reference, args.distorted)
        text = json.dumps(result, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except (QualityError, OSError, ValueError) as exc:
        print(f"quality: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
