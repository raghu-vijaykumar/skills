"""CLI for the plan -> timeline -> human approval -> single render path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from approval import capability_sha256, fingerprint, require_human_approval
from compiler import compile_graph, media_info, preview, render
from model import (load, make_initial, revise, sha256_file,
                   snapshot_preflight, validate, write_new)
from verify import verify_output


def summary(resolved: dict) -> dict:
    return {
        "duration": round(resolved["duration"], 3),
        "picture": [
            {"id": clip["id"], "source": clip["source"],
             "timeline_start": round(clip["start"], 3),
             "timeline_end": round(clip["end"], 3),
             "source_in": clip["source_in"], "source_out": clip["source_out"]}
            for clip in resolved["clips"]
        ],
        "operations": resolved["operations"],
        "audio": resolved["audio"],
        "transitions": list(resolved["transitions"].values()),
        "output": str(resolved["output"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    init = commands.add_parser("init", help="Create a draft from an approved plan")
    init.add_argument("--plan", type=Path, required=True)
    init.add_argument("--source", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--timeline", type=Path, required=True)
    init.add_argument("--fps", type=int, default=30)
    init.add_argument("--width", type=int, default=1920)
    init.add_argument("--height", type=int, default=1080)
    hash_asset = commands.add_parser("hash", help="Hash an input asset for a timeline")
    hash_asset.add_argument("--file", type=Path, required=True)
    for name in ("validate", "fingerprint", "preview", "render"):
        action = commands.add_parser(name)
        action.add_argument("--timeline", type=Path, required=True)
        if name == "render":
            action.add_argument("--approval", type=Path, required=True)
        if name == "preview":
            action.add_argument("--output", type=Path, required=True)
            action.add_argument("--start", type=float, required=True)
            action.add_argument("--duration", type=float, required=True)
    change = commands.add_parser("revise", help="Write an immutable successor")
    change.add_argument("--timeline", type=Path, required=True)
    change.add_argument("--plan", type=Path, required=True,
                        help="Current human-approved edited-render preflight plan")
    change.add_argument("--changes", type=Path, required=True)
    change.add_argument("--out", type=Path, required=True)
    change.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify", help="Check the exact delivered file")
    verify.add_argument("--record", type=Path, required=True)
    verify.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "hash":
            if not args.file.is_file():
                raise ValueError("Asset file is missing")
            result = {"file": str(args.file.resolve()),
                      "sha256": sha256_file(args.file)}
        elif args.action == "init":
            if args.timeline.exists():
                raise ValueError("Timeline revision already exists")
            timeline = make_initial(args.plan, args.source, args.output,
                                    fps=args.fps, width=args.width,
                                    height=args.height)
            info = media_info(args.source)
            if not info["video"] or info["duration"] <= 0:
                raise ValueError("Input must contain a video stream")
            timeline["picture"][0]["source_out"] = round(info["duration"], 6)
            resolved = validate(timeline)
            compile_graph(timeline, resolved)
            timeline["plan_file"] = str(snapshot_preflight(args.plan, args.timeline))
            resolved = validate(timeline)
            write_new(args.timeline, timeline)
            result = {"timeline": str(args.timeline), **summary(resolved)}
        elif args.action == "revise":
            if args.out.exists():
                raise ValueError("Timeline revision already exists")
            old = load(args.timeline)
            validate(old, require_review=False)
            changes = load(args.changes)
            timeline = revise(old, changes, new_output=str(args.output))
            # Every revision goes through the current approved plan again.
            timeline["plan_file"] = str(args.plan.resolve())
            timeline["plan_sha256"] = sha256_file(args.plan)
            resolved = validate(timeline, require_review=False)
            compile_graph(timeline, resolved)
            timeline["plan_file"] = str(snapshot_preflight(args.plan, args.out))
            resolved = validate(timeline, require_review=False)
            write_new(args.out, timeline)
            result = {"timeline": str(args.out), **summary(resolved)}
        elif args.action == "verify":
            result = verify_output(args.record, args.evidence_dir)
        else:
            timeline = load(args.timeline)
            resolved = validate(timeline, require_review=args.action in
                                {"fingerprint", "render"})
            compile_graph(timeline, resolved)
            if args.action == "validate":
                result = summary(resolved)
            elif args.action == "preview":
                result = preview(timeline, resolved, args.output,
                                 args.start, args.duration)
            elif args.action == "fingerprint":
                result = {"fingerprint": fingerprint(args.timeline, timeline)}
            elif args.action == "render":
                approval = require_human_approval(
                    args.timeline, timeline, args.approval)
                record_path = resolved["output"].with_suffix(
                    resolved["output"].suffix + ".render.json")
                if record_path.exists():
                    raise ValueError("Render record already exists")
                record = render(timeline, resolved)
                record.update({
                    "timeline": str(args.timeline.resolve()),
                    "timeline_sha256": sha256_file(args.timeline),
                    "approval": str(args.approval.resolve()),
                    "approval_sha256": sha256_file(args.approval),
                    "approval_fingerprint": approval["fingerprint"],
                    "capability_sha256": capability_sha256(),
                    "revision": timeline["revision"],
                })
                write_new(record_path, record)
                result = {"record": str(record_path), **record}
            else:
                raise AssertionError(args.action)
        print(json.dumps(result, indent=2, default=str))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        parser.exit(2, f"Timeline {args.action} failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
