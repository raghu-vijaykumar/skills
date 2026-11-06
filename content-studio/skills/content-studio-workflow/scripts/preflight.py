#!/usr/bin/env python3
"""Prepare and gate a reviewed, draft-specific Content Studio production plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PLAN_DIR = Path(".content-studio/preflight")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"Missing {path}; run preflight init first")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def plan_hash(plan_file: Path) -> str:
    # Hash the actual review file, so even formatting or numeric JSON changes make approval stale.
    return hashlib.sha256(plan_file.read_bytes()).hexdigest()


def paths(draft: Path) -> tuple[Path, Path, Path, Path]:
    base = draft / PLAN_DIR
    return base / "system.json", base / "plan.json", base / "approval.json", base / "checklist.json"


def run_quiet(argv: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)


def memory_gib() -> float | None:
    if os.name == "nt":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
                        ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                        ("available_extended", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return round(status.total_physical / 2**30, 1)
    elif Path("/proc/meminfo").is_file():
        first = Path("/proc/meminfo").read_text().splitlines()[0].split()
        return round(int(first[1]) * 1024 / 2**30, 1)
    return None


def probe(sample: Path) -> dict:
    result = run_quiet(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=index,codec_type,width,height,avg_frame_rate,pix_fmt,color_transfer,color_primaries,color_space,side_data_list",
                        "-of", "json", str(sample)])
    if result.returncode:
        raise ValueError(f"ffprobe failed: {result.stderr.strip()[-500:]}")
    data = json.loads(result.stdout)
    video = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("Sample has no video stream")
    fps_text = video.get("avg_frame_rate", "0/1")
    numerator, denominator = (float(part) for part in fps_text.split("/"))
    transfer = video.get("color_transfer", "unknown")
    side_data = json.dumps(video.get("side_data_list", []))
    return {"path": str(sample), "duration_seconds": round(float(data.get("format", {}).get("duration", 0)), 2),
            "width": video.get("width"), "height": video.get("height"),
            "fps": round(numerator / denominator, 3) if denominator else None,
            "pixel_format": video.get("pix_fmt"), "color_transfer": transfer,
            "color_primaries": video.get("color_primaries"), "color_space": video.get("color_space"),
            "hdr_or_dv": transfer in {"arib-std-b67", "smpte2084"} or "DOVI" in side_data.upper()}


def timed_ffmpeg(sample: Path, filter_graph: str | None, seconds: float = 2.0) -> dict:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", "0", "-i", str(sample),
               "-t", str(seconds), "-an"]
    if filter_graph:
        command += ["-vf", filter_graph]
    command += ["-f", "null", os.devnull]
    start = time.monotonic()
    try:
        result = run_quiet(command, timeout=90)
        return {"seconds": round(time.monotonic() - start, 3), "sample_seconds": seconds,
                "ok": result.returncode == 0, "error": result.stderr.strip()[-300:] if result.returncode else ""}
    except subprocess.TimeoutExpired:
        return {"seconds": None, "sample_seconds": seconds, "ok": False, "error": "90-second timeout"}


def profile(draft: Path, sample: Path | None, planned_minutes: float | None,
            ai_seconds_per_frame: float | None) -> dict:
    # The bounded FFmpeg runs characterize this machine; AI inference needs its own representative pilot.
    tools = {name: shutil.which(name) for name in ("ffmpeg", "ffprobe", "nvidia-smi", "realesrgan-ncnn-vulkan")}
    disk = shutil.disk_usage(draft)
    report = {"captured_at": timestamp(), "machine": {"os": platform.platform(),
              "cpu_logical": os.cpu_count(), "memory_gib": memory_gib(),
              "free_disk_gib": round(disk.free / 2**30, 1)}, "tools": tools,
              "sample": None, "benchmarks": {}, "estimates": {}, "recommendations": []}
    if tools["nvidia-smi"]:
        gpu = run_quiet([tools["nvidia-smi"], "--query-gpu=name,memory.total", "--format=csv,noheader"], timeout=10)
        if gpu.returncode == 0:
            report["machine"]["gpu"] = gpu.stdout.strip().splitlines()
    if sample:
        if not sample.is_file() or not tools["ffprobe"]:
            raise ValueError("A readable sample and ffprobe are required for media profiling")
        report["sample"] = probe(sample)
        media = report["sample"]
        if tools["ffmpeg"]:
            measured_seconds = min(2.0, media["duration_seconds"]) if media["duration_seconds"] > 0 else 2.0
            report["benchmarks"]["decode_2s"] = timed_ffmpeg(sample, None, measured_seconds)
            report["benchmarks"]["lanczos_2s"] = timed_ffmpeg(sample, "scale=3840:2160:flags=lanczos", measured_seconds)
        if planned_minutes:
            frames = planned_minutes * 60 * (media["fps"] or 30)
            if ai_seconds_per_frame:
                report["estimates"]["ai_upscale_hours"] = round(frames * ai_seconds_per_frame / 3600, 2)
                report["estimates"]["basis"] = "supplied representative AI seconds per frame; sustained throughput may differ"
                if report["estimates"]["ai_upscale_hours"] >= 2:
                    report["recommendations"].append("AI upscale is a multi-hour route on the supplied pilot: limit it to verified FIX ranges, benchmark sustained throughput, and review storage/thermal headroom before a long render.")
            else:
                report["estimates"]["ai_upscale_hours"] = None
                report["estimates"]["basis"] = "run a short AI pilot on this machine before estimating full duration"
            for key in ("decode_2s", "lanczos_2s"):
                bench = report["benchmarks"].get(key, {})
                if bench.get("ok"):
                    report["estimates"][key.replace("_2s", "_hours")] = round(bench["seconds"] * planned_minutes * 60 / bench["sample_seconds"] / 3600, 2)
        if media["hdr_or_dv"]:
            report["recommendations"].append("HDR/Dolby Vision: preserve source; decide tone mapping before any upscale or color render.")
        elif (media["width"] or 0) < 3840:
            report["recommendations"].append("If delivery needs 4K, compare a short Lanczos and live-action AI preview; use AI only for verified gains on used timeline ranges.")
        else:
            report["recommendations"].append("Source is already 4K width; diagnose detail before proposing upscale.")
    else:
        report["recommendations"].append("No sample supplied; media-specific routes and time estimates remain unverified.")
    report["recommendations"].append("Diagnose color first; preview a bounded correction and compare the exact affected output before committing to a grade.")
    report["recommendations"].append("For review, produce a small contact sheet or short frame/clip preview; streaming frames is an optional review route, never the sole quality gate.")
    return report


def default_steps(kind: str) -> list[dict]:
    production = "Preprocess and review source clips; build a rough cut" if kind == "edited" else "Author scenes and narration-timed visuals"
    return [
        {"id": "S01", "title": "Review sources and rights", "route": "Inspect source, channel rules, existing work and approvals", "estimated_time": "Estimate after intake", "output": "source and rights notes", "acceptance": "Source and usage constraints recorded", "required": True},
        {"id": "S02", "title": "Approve story and visual treatment", "route": "Set teaching beats, framing, style, deliverables and human review points", "estimated_time": "Estimate after outline", "output": "approved brief or outline", "acceptance": "Creative direction agreed", "required": True},
        {"id": "S03", "title": "Create and inspect edit", "route": production, "estimated_time": "Estimate from footage or scene count", "output": "reviewable cut or scene preview", "acceptance": "Timing and key visuals reviewed", "required": True},
        {"id": "S04", "title": "Diagnose upscale and color", "route": "Use system profile and short source-linked previews; choose SKIP/FIX/REVIEW per issue; favor used timeline ranges", "estimated_time": "See system profile; AI unknown until pilot", "output": "comparison frames/clips and decision report", "acceptance": "Measured gains and side effects reviewed; HDR/DV handled explicitly", "required": True},
        {"id": "S05", "title": "Review audio and music", "route": "Diagnose, compare bounded candidates, verify selected master", "estimated_time": "Estimate after audio diagnosis", "output": "audio review evidence", "acceptance": "Listening and loudness checks complete", "required": True},
        {"id": "S06", "title": "Review exact final render", "route": "Watch the complete export and affected ranges", "estimated_time": "At least full runtime plus inspection", "output": "final master and review note", "acceptance": "Human reviewed delivered frames and audio", "required": True},
        {"id": "S07", "title": "Prepare publication package", "route": "Derive metadata from evidence; review thumbnail, rights, credits and package", "estimated_time": "Estimate after metadata review", "output": "title, description, thumbnail and package review", "acceptance": "Publication candidate reviewed; publishing separately authorized", "required": True},
    ]


def validate_plan(plan: dict) -> None:
    if plan.get("schema_version") != 1 or plan.get("kind") not in {"edited", "remotion"}:
        raise ValueError("Plan needs schema_version 1 and kind edited or remotion")
    for field in ("goal", "inputs", "deliverables", "steps", "system_profile"):
        if not plan.get(field):
            raise ValueError(f"Plan needs {field}")
    if not isinstance(plan["steps"], list):
        raise ValueError("Plan steps must be a list")
    ids = set()
    for step in plan["steps"]:
        if not isinstance(step, dict) or any(not str(step.get(key, "")).strip() for key in ("id", "title", "route", "estimated_time", "output", "acceptance")):
            raise ValueError("Every step needs id, title, route, estimated_time, output and acceptance")
        if step["id"] in ids:
            raise ValueError(f"Duplicate step ID: {step['id']}")
        ids.add(step["id"])
    for title in ("Review sources and rights", "Review exact final render"):
        if not any(step["title"] == title and step.get("required") is True for step in plan["steps"]):
            raise ValueError(f"Required review step missing: {title}")


def approved(draft: Path) -> tuple[dict, dict, dict]:
    _, plan_file, approval_file, checklist_file = paths(draft)
    plan = read_json(plan_file)
    validate_plan(plan)
    if not approval_file.is_file():
        raise ValueError("Preflight approval is missing; show the plan for human review first")
    approval = read_json(approval_file)
    digest = plan_hash(plan_file)
    if approval.get("plan_sha256") != digest or not approval.get("review_note"):
        raise ValueError("Preflight approval is missing or stale; review the edited plan again")
    checklist = read_json(checklist_file)
    if checklist.get("plan_sha256") != digest or [item.get("id") for item in checklist.get("items", [])] != [step["id"] for step in plan["steps"]]:
        raise ValueError("Preflight checklist does not match the approved plan")
    return plan, approval, checklist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, type=Path, help="existing draft directory")
    sub = parser.add_subparsers(dest="command", required=True)
    profile_parser = sub.add_parser("profile")
    profile_parser.add_argument("--sample", type=Path)
    profile_parser.add_argument("--planned-minutes", type=float)
    profile_parser.add_argument("--ai-seconds-per-frame", type=float)
    init = sub.add_parser("init")
    init.add_argument("--kind", required=True, choices=("edited", "remotion"))
    init.add_argument("--goal", required=True)
    init.add_argument("--input", action="append", required=True, dest="inputs")
    init.add_argument("--deliverable", action="append", required=True, dest="deliverables")
    sub.add_parser("review")
    approve = sub.add_parser("approve")
    approve.add_argument("--note", required=True, help="record the user's explicit review decision")
    update = sub.add_parser("set")
    update.add_argument("--id", required=True)
    update.add_argument("--status", required=True, choices=("done", "not_applicable"))
    update.add_argument("--evidence", action="append", default=[])
    update.add_argument("--reason", default="")
    verify = sub.add_parser("verify")
    verify.add_argument("--phase", choices=("start", "complete"), default="start")
    args = parser.parse_args(argv)
    draft = args.folder.expanduser().resolve()
    if not draft.is_dir():
        raise ValueError(f"Draft folder not found: {draft}")
    system_file, plan_file, approval_file, checklist_file = paths(draft)
    if args.command == "profile":
        if args.planned_minutes is not None and args.planned_minutes <= 0:
            raise ValueError("--planned-minutes must be positive")
        if args.ai_seconds_per_frame is not None and args.ai_seconds_per_frame <= 0:
            raise ValueError("--ai-seconds-per-frame must be positive")
        report = profile(draft, args.sample.expanduser().resolve() if args.sample else None,
                         args.planned_minutes, args.ai_seconds_per_frame)
        write_json(system_file, report)
        print(json.dumps(report, indent=2))
        return 0
    if args.command == "init":
        if plan_file.exists():
            raise ValueError(f"Plan exists: {plan_file}; edit it and request another review")
        system = read_json(system_file)
        plan = {"schema_version": 1, "kind": args.kind, "goal": args.goal.strip(),
                "inputs": args.inputs, "deliverables": args.deliverables,
                "system_profile": system, "steps": default_steps(args.kind),
                "notes": "Edit routes, steps, estimates and review criteria before asking for approval."}
        validate_plan(plan)
        write_json(plan_file, plan)
        print(plan_file)
        return 0
    if args.command == "review":
        plan = read_json(plan_file)
        validate_plan(plan)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        print("Await explicit human review before approve; plan edits invalidate prior approval.")
        return 0
    if args.command == "approve":
        plan = read_json(plan_file)
        validate_plan(plan)
        note = args.note.strip()
        if not note:
            raise ValueError("Human review note is required")
        digest = plan_hash(plan_file)
        write_json(approval_file, {"approved_at": timestamp(), "review_note": note, "plan_sha256": digest})
        # A changed plan starts a fresh checklist so old completion evidence cannot carry across revisions.
        write_json(checklist_file, {"plan_sha256": digest, "items": [
            {"id": step["id"], "status": "pending", "evidence": [], "reason": ""} for step in plan["steps"]]})
        print(f"Approved {digest}; checklist reset to {len(plan['steps'])} pending steps")
        return 0
    plan, _, checklist = approved(draft)
    if args.command == "set":
        step = next((step for step in plan["steps"] if step["id"] == args.id), None)
        item = next((item for item in checklist["items"] if item["id"] == args.id), None)
        if step is None or item is None:
            raise ValueError(f"Unknown step: {args.id}")
        evidence = [entry.strip() for entry in args.evidence if entry.strip()]
        if args.status == "done" and not evidence:
            raise ValueError("Done needs at least one evidence path or review note")
        if args.status == "not_applicable" and (step.get("required") or not args.reason.strip()):
            raise ValueError("Only optional steps may be not_applicable, with a reason")
        item.update({"status": args.status, "evidence": evidence, "reason": args.reason.strip(), "updated_at": timestamp()})
        write_json(checklist_file, checklist)
        print(f"{args.id}: {args.status}")
        return 0
    if args.command == "verify":
        if args.phase == "complete":
            incomplete = [item["id"] for step, item in zip(plan["steps"], checklist["items"])
                          if not ((item.get("status") == "done" and item.get("evidence")) or
                                  (item.get("status") == "not_applicable" and not step.get("required") and item.get("reason")))]
            if incomplete:
                raise ValueError("Preflight checklist incomplete: " + ", ".join(incomplete))
        print(f"Preflight {args.phase} gate passed: {len(checklist['items'])} approved steps")
        return 0
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"preflight: {error}") from error
