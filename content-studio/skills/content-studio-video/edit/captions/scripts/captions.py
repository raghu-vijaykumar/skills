"""Prepare reviewed, opt-in ASS captions for the Content Studio delivery timeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

from PIL import ImageFont


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Caption asset must be inside source root: {path}") from exc


def _ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    whole, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole:02d}.{fraction:02d}"


def _require_approved_preflight(draft: Path) -> None:
    script = Path(__file__).resolve().parents[4] / "content-studio-workflow" / "scripts" / "preflight.py"
    spec = importlib.util.spec_from_file_location("content_studio_preflight", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Content Studio preflight is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan, _, _ = module.approved(draft.resolve())
    if not any(step.get("method_id") == "captions-ass" for step in plan["steps"]):
        raise ValueError("Approved preflight plan does not include captions-ass")


def validate_sheet(sheet: dict, root: Path) -> dict:
    """Reject ambiguous timing and text that would extend outside the caption area."""
    width, height = sheet.get("width"), sheet.get("height")
    duration = sheet.get("duration_seconds")
    if (not isinstance(width, int) or not isinstance(height, int)
            or width < 64 or height < 64
            or not isinstance(duration, (int, float)) or duration <= 0):
        raise ValueError("Caption sheet needs positive duration and canvas dimensions")
    font_name = sheet.get("font_name")
    font_source = Path(sheet.get("font_source", ""))
    if (not isinstance(font_name, str) or not font_name.strip()
            or any(character in font_name for character in ",\r\n{}")):
        raise ValueError("Caption sheet needs a named, readable font_source")
    font_path = (root / font_source).resolve() if not font_source.is_absolute() else font_source.resolve()
    _relative(font_path, root)
    if not font_path.is_file():
        raise ValueError("Caption font is missing")
    size = sheet.get("font_size", round(height * .052))
    margin = sheet.get("margin_bottom_fraction", .1)
    if (not isinstance(size, int) or not height * .025 <= size <= height * .08
            or not isinstance(margin, (int, float)) or not .06 <= margin <= .18):
        raise ValueError("Caption font size or bottom safe-zone margin is invalid")
    font = ImageFont.truetype(str(font_path), size)
    cues = sheet.get("cues")
    if not isinstance(cues, list) or not cues:
        raise ValueError("Requested captions need at least one cue")
    previous_end = 0.0
    normalized = []
    for index, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise ValueError(f"Caption cue {index} is invalid")
        start, end, text = cue.get("start"), cue.get("end"), cue.get("text")
        if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                or not 0 <= start < end <= duration or start < previous_end - .001
                or end - start < .1):
            raise ValueError(f"Caption cue {index} timing is invalid or overlaps")
        if (not isinstance(text, str) or not text.strip() or len(text) > 160
                or any(character in text for character in "{}\\\r\t")
                or any(ord(character) < 32 and character != "\n" for character in text)):
            raise ValueError(f"Caption cue {index} text is invalid")
        lines = text.split("\n")
        if (len(lines) > 2 or any(not line.strip() for line in lines)
                or any(font.getlength(line) > width * .78 for line in lines)):
            raise ValueError(f"Caption cue {index} exceeds the two-line safe area")
        if len(lines) * size * 1.25 + height * margin > height * .28:
            raise ValueError(f"Caption cue {index} exceeds the lower safe area")
        # ASS stores centiseconds. Refuse cues that would collapse after rounding.
        if round(start * 100) >= round(end * 100):
            raise ValueError(f"Caption cue {index} collapses at ASS time resolution")
        normalized.append({"start": round(start, 2), "end": round(end, 2),
                           "text": text.strip()})
        previous_end = end
    return {"width": width, "height": height, "duration_seconds": float(duration),
            "font_name": font_name.strip(), "font_source": _relative(font_path, root),
            "font_sha256": sha256_file(font_path), "font_size": size,
            "margin_bottom_fraction": float(margin), "cues": normalized}


def create(sheet_path: Path, root: Path, sidecar: Path, handoff: Path,
           draft: Path) -> dict:
    _require_approved_preflight(draft)
    sheet = validate_sheet(json.loads(sheet_path.read_text(encoding="utf-8")), root)
    source = _relative(sidecar, root)
    margin_x = round(sheet["width"] * .1)
    margin_y = round(sheet["height"] * sheet["margin_bottom_fraction"])
    style = ("Style: Caption,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,"
             "&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,{mx},{mx},{my},1").format(
                 font=sheet["font_name"], size=sheet["font_size"], mx=margin_x, my=margin_y)
    lines = ["[Script Info]", "ScriptType: v4.00+",
             f"PlayResX: {sheet['width']}", f"PlayResY: {sheet['height']}",
             "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
             "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
             "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
             "MarginL, MarginR, MarginV, Encoding", style, "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for cue in sheet["cues"]:
        text = cue["text"].replace("\n", r"\N")
        lines.append(f"Dialogue: 0,{_ass_time(cue['start'])},{_ass_time(cue['end'])},"
                     f"Caption,,0,0,0,,{text}")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text("\n".join(lines) + "\n", encoding="utf-8")
    operation = {"id": "captions", "method": "motion-graphics-ass", "source": source,
                 "sha256": sha256_file(sidecar), "font_source": sheet["font_source"],
                 "font_sha256": sheet["font_sha256"], "start": 0,
                 "end": sheet["duration_seconds"], "review_status": "pending_review"}
    report = {"sheet_sha256": sha256_file(sheet_path), "operation": operation,
              "cues": sheet["cues"], "human_review_required": True}
    handoff.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def preview(source: Path, sidecar: Path, font: Path, output: Path,
            start: float, duration: float) -> None:
    if not source.is_file() or not sidecar.is_file() or not font.is_file():
        raise ValueError("Preview source, sidecar or font is missing")
    if start < 0 or not 0 < duration <= 5:
        raise ValueError("Caption preview must be a bounded 0-5 second interval")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Resolve ASS and its font relative to the same root used by the final timeline.
    from_root = sidecar.parent
    relative_font_dir = os.path.relpath(font.parent, from_root)
    ass = sidecar.name.replace(":", "\\:")
    font_dir = str(relative_font_dir).replace("\\", "/").replace(":", "\\:")
    result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                             "-ss", str(start), "-t", str(duration), "-i", str(source),
                             "-vf", f"ass={ass}:fontsdir={font_dir}",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(output)],
                            cwd=from_root, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    for flag in ("sheet", "root", "sidecar", "handoff", "draft"):
        create_parser.add_argument(f"--{flag}", required=True, type=Path)
    preview_parser = commands.add_parser("preview")
    for flag in ("source", "sidecar", "font", "output"):
        preview_parser.add_argument(f"--{flag}", required=True, type=Path)
    preview_parser.add_argument("--start", type=float, required=True)
    preview_parser.add_argument("--duration", type=float, required=True)
    args = parser.parse_args()
    if args.command == "create":
        print(json.dumps(create(args.sheet, args.root, args.sidecar, args.handoff, args.draft), indent=2,
                         ensure_ascii=False))
    else:
        preview(args.source.resolve(), args.sidecar.resolve(), args.font.resolve(),
                args.output.resolve(), args.start, args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
