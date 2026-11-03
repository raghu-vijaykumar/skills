#!/usr/bin/env python3
"""Deterministic lifecycle checklist for a Content Studio draft.

The main content-studio router initializes this checklist. Direct specialist
skills do not create it and remain one-off tools.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BUNDLE_ROOT / "skills" / "content-studio-videoedit" / "scripts"))

from common import DEFAULT_CONFIG, channel_root, load_config, select_channels  # noqa: E402

CHECKLIST = "lifecycle-checklist.json"
STATUSES = ("pending", "done", "not_applicable", "deferred")
KINDS = ("edited", "remotion")

# Fixed order and fixed IDs. Do not renumber existing items.
ITEMS = [
    ("C01", "intake", "Channel and draft rules reviewed", "pre_publish", "all",
     "Read the channel owner rules, current draft, and any existing approval."),
    ("C02", "intake", "Production kind recorded", "pre_publish", "all",
     "The draft is explicitly edited or remotion, and draft.json agrees."),
    ("C03", "idea", "Idea brief or story outline approved", "pre_publish", "all",
     "An approved brief/outline exists, or this is explicitly not applicable to a supplied edit."),
    ("C04", "footage", "Camera clips preprocessed", "pre_publish", "edited",
     "Duplicates quarantined, clips ordered, blur/Dolby Vision gates reviewed, and clean or final exports available."),
    ("C05", "rough_cut", "AutoCut rough cut reviewed", "pre_publish", "edited",
     "A human reviewed the rough cut and review media (including reframe previews when used), the target orientation/fit is recorded, or AutoCut was explicitly deferred."),
    ("C06", "audio", "Audio mastered and reviewed", "pre_publish", "all",
     "Loudness and dynamics checked; use not applicable only when no audio treatment is needed."),
    ("C07", "edit", "Master edit or render complete", "pre_publish", "all",
     "A full-length master exists and has been watched end to end."),
    ("C08", "color", "Color, HDR, and Dolby Vision reviewed", "pre_publish", "all",
     "SDR tags and tone mapping checked; Dolby Vision proof reviewed when applicable."),
    ("C09", "transcript", "Transcript reviewed", "pre_publish", "edited",
     "transcript.json matches the master hash and the spoken content."),
    ("C10", "captions", "Captions reviewed", "pre_publish", "edited",
     "captions.srt timing and text reviewed, or captions explicitly declined."),
    ("C11", "thumbnail", "Thumbnail approved", "pre_publish", "all",
     "An approved thumbnail exists at the platform size and limit."),
    ("C12", "music", "Music selected, mixed, and licensed", "pre_publish", "all",
     "music-selection.json, music-credits.txt, and a reviewed music-mixed master exist, or the draft explicitly has no music."),
    ("C13", "metadata", "Title and description reviewed", "pre_publish", "all",
     "Exact title and description reviewed, including required music attribution."),
    ("C14", "rights", "Rights, licenses, and consent reviewed", "pre_publish", "all",
     "Footage, music, fonts, logos, faces, locations, and client data are cleared for publication."),
    ("C15", "creative", "Creative metadata recorded", "pre_publish", "all",
     "creative.json has themeId, styleId, format, renderer, and choices."),
    ("C16", "approval", "Package approval recorded", "pre_publish", "all",
     "package-approval.json matches the current publication files."),
    ("C17", "publish_plan", "Publish plan previewed", "pre_publish", "all",
     "Platform, visibility, schedule, title, description, thumbnail, and captions previewed."),
    ("C18", "publish", "Published or scheduled with receipt", "post_publish", "all",
     "Platform ID and receipt recorded in draft.json; uncertain results reconciled before retry."),
    ("C19", "verify", "Public or scheduled status verified", "post_publish", "all",
     "The live/scheduled status matches the intended visibility and schedule."),
    ("C20", "archive", "Public YouTube backup completed", "post_publish", "all",
     "Backup contains the public video, exact metadata, thumbnail, and publish receipt."),
    ("C21", "drive", "Drive sync verified", "post_publish", "all",
     "rclone check evidence confirms the durable media copy."),
    ("C22", "close", "Draft handoff or close recorded", "post_publish", "all",
     "The draft is moved or closed under channel policy and the source remains retained."),
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def item_defaults(kind: str) -> list[dict]:
    items = []
    for item_id, stage, title, phase, applies_to, criteria in ITEMS:
        status, reason = "pending", ""
        if phase == "post_publish":
            status, reason = "deferred", "post-publish gate"
        elif applies_to == "edited" and kind == "remotion":
            status, reason = "not_applicable", "Remotion production has no camera footage"
        elif applies_to == "remotion" and kind == "edited":
            status, reason = "not_applicable", "Edited production does not use this Remotion step"
        items.append({
            "id": item_id,
            "stage": stage,
            "title": title,
            "phase": phase,
            "applies_to": applies_to,
            "criteria": criteria,
            "status": status,
            "reason": reason,
            "evidence": [],
            "note": "",
            "updated_at": now(),
            "updated_by": "system",
        })
    return items


def checklist_path(draft: Path) -> Path:
    return draft / CHECKLIST


def load_checklist(draft: Path) -> dict:
    path = checklist_path(draft)
    if not path.is_file():
        raise SystemExit(f"no lifecycle checklist: {path}\nRun checklist.py init first.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("items"), list) or not data["items"]:
        raise SystemExit(f"invalid lifecycle checklist: {path}")
    return data


def save_checklist(draft: Path, data: dict) -> None:
    data["updated_at"] = now()
    path = checklist_path(draft)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mark_main_lifecycle(draft: Path, kind: str) -> dict:
    path = draft / "draft.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    production = manifest.setdefault("production", {})
    existing = production.get("kind")
    if existing and existing != kind:
        raise SystemExit(f"draft.json says production.kind={existing}; pass --kind {existing} or use --force")
    production["kind"] = kind
    manifest["lifecycle"] = "main"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def init_checklist(draft: Path, channel: str, kind: str, force: bool = False) -> tuple[dict, bool]:
    if kind not in KINDS:
        raise SystemExit(f"--kind must be one of: {', '.join(KINDS)}")
    mark_main_lifecycle(draft, kind)
    path = checklist_path(draft)
    if path.exists() and not force:
        return load_checklist(draft), False
    data = {
        "schema_version": 1,
        "channel": channel,
        "draft": draft.name,
        "kind": kind,
        "created_at": now(),
        "updated_at": now(),
        "items": item_defaults(kind),
    }
    save_checklist(draft, data)
    return data, True


def find_item(data: dict, item_id: str) -> dict:
    wanted = item_id.strip().upper()
    for item in data["items"]:
        if item["id"].upper() == wanted:
            return item
    raise SystemExit(f"unknown checklist item: {item_id}")


def update_item(draft: Path, item_id: str, status: str, *, reason: str = "",
                evidence: list[str] | None = None, note: str = "",
                by: str = "agent") -> dict:
    if status not in STATUSES:
        raise SystemExit(f"--status must be one of: {', '.join(STATUSES)}")
    data = load_checklist(draft)
    item = find_item(data, item_id)
    evidence = [value for value in (evidence or []) if value.strip()]
    if status == "done" and not evidence and not note.strip():
        raise SystemExit(f"{item['id']}: done requires --evidence or --note")
    if status in {"not_applicable", "deferred"} and not (reason.strip() or note.strip()):
        raise SystemExit(f"{item['id']}: {status} requires --reason")
    item["status"] = status
    item["reason"] = reason.strip() or (note.strip() if status in {"not_applicable", "deferred"} else "")
    item["evidence"] = evidence
    item["note"] = note.strip()
    item["updated_at"] = now()
    item["updated_by"] = by
    save_checklist(draft, data)
    return item


def verify_checklist(data: dict, phase: str) -> list[str]:
    if phase not in {"pre_publish", "all"}:
        raise SystemExit("--phase must be pre_publish or all")
    selected = [item for item in data["items"]
                if phase == "all" or item.get("phase") == "pre_publish"]
    failures = []
    for item in selected:
        status = item.get("status")
        if status == "done":
            if not item.get("evidence") and not str(item.get("note", "")).strip():
                failures.append(f"{item['id']}: done without evidence or note")
        elif status == "not_applicable":
            if not str(item.get("reason", "")).strip():
                failures.append(f"{item['id']}: not_applicable without reason")
        elif status == "deferred":
            failures.append(f"{item['id']}: deferred ({item.get('reason') or 'no reason'})")
        else:
            failures.append(f"{item['id']}: {status or 'pending'}")
    return failures


def print_status(data: dict) -> None:
    print(f"{'ID':<4} {'PHASE':<12} {'STATUS':<15} {'TITLE':<44} DETAIL")
    for item in data["items"]:
        detail = item.get("reason") or item.get("note") or ", ".join(item.get("evidence", []))
        print(f"{item['id']:<4} {str(item.get('phase', '')):<12} {str(item.get('status', '')):<15} "
              f"{str(item.get('title', ''))[:44]:<44} {str(detail)[:72]}")
    counts = {status: sum(1 for item in data["items"] if item.get("status") == status)
              for status in STATUSES}
    print("summary: " + ", ".join(f"{key}={value}" for key, value in counts.items()))


def resolve_draft(args) -> tuple[str, Path]:
    if not args.channel or not args.draft:
        raise SystemExit("--channel and --draft are required")
    cfg = load_config(Path(args.config))
    slug, _ = select_channels(cfg, args.channel)[0]
    draft = channel_root(cfg, slug) / "drafts" / args.draft
    if not draft.is_dir():
        raise SystemExit(f"draft not found: {draft}")
    return slug, draft


def inferred_kind(draft: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    path = draft / "draft.json"
    if path.is_file():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        kind = manifest.get("production", {}).get("kind")
        if kind in KINDS:
            return kind
    raise SystemExit("pass --kind edited or --kind remotion")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic lifecycle checklist for a Content Studio draft.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--channel")
    parser.add_argument("--draft")
    parser.add_argument("--kind", choices=KINDS)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", default=argparse.SUPPRESS)
    shared.add_argument("--channel", default=argparse.SUPPRESS)
    shared.add_argument("--draft", default=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", parents=[shared],
                          help="create or load the draft checklist")
    init.add_argument("--kind", choices=KINDS, default=argparse.SUPPRESS)
    init.add_argument("--force", action="store_true", help="reset all statuses")

    update = sub.add_parser("set", parents=[shared],
                            help="update one checklist item")
    update.add_argument("--id", required=True, dest="item_id")
    update.add_argument("--status", required=True, choices=STATUSES)
    update.add_argument("--reason", default="")
    update.add_argument("--evidence", action="append", default=[])
    update.add_argument("--note", default="")
    update.add_argument("--by", default="agent")

    status = sub.add_parser("status", parents=[shared],
                            help="show the checklist")
    status.add_argument("--json", action="store_true")

    verify = sub.add_parser("verify", parents=[shared],
                            help="fail if required items are not covered")
    verify.add_argument("--phase", choices=["pre_publish", "all"], default="pre_publish")
    verify.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    slug, draft = resolve_draft(args)

    if args.command == "init":
        kind = inferred_kind(draft, args.kind)
        data, created = init_checklist(draft, slug, kind, force=args.force)
        print(f"{'created' if created else 'existing'}: {checklist_path(draft)}")
        print_status(data)
        return 0

    if args.command == "set":
        item = update_item(draft, args.item_id, args.status, reason=args.reason,
                           evidence=args.evidence, note=args.note, by=args.by)
        print(f"{item['id']}: {item['status']}")
        return 0

    data = load_checklist(draft)
    if args.command == "status":
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print_status(data)
        return 0

    if args.command == "verify":
        failures = verify_checklist(data, args.phase)
        if args.json:
            print(json.dumps({"phase": args.phase, "ready": not failures,
                              "failures": failures}, indent=2))
        elif failures:
            print(f"checklist not ready ({args.phase}):")
            for failure in failures:
                print(f"  {failure}")
        else:
            print(f"checklist ready ({args.phase})")
        return 1 if failures else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
