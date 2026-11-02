"""rclone helpers: one-way copies that never delete the remote."""

from __future__ import annotations

import subprocess
from pathlib import Path

from common import Log, run_stream

ARCHIVE_EXCLUDES = ["--exclude", "*.log", "--exclude", "backup-report.json",
                    "--exclude", ".staging/**", "--exclude", "*.part"]


def available() -> bool:
    from shutil import which

    return bool(which("rclone"))


def join(remote: str, *parts: str) -> str:
    remote = remote.rstrip("/")
    tail = "/".join(p.strip("/") for p in parts if p)
    return f"{remote}/{tail}" if tail else remote


def copy(local: Path, target: str, log: Log, transfers: int = 2,
         immutable: bool = False) -> int:
    """Copy local -> target. immutable=True skips anything already on the target."""
    if not target:
        log("no Drive folder configured; local only")
        return 0
    cmd = ["rclone", "copy", str(local), target,
           "--transfers", str(transfers), "--checkers", "8",
           "--drive-chunk-size", "64M", "--stats", "60s", "--stats-one-line",
           *ARCHIVE_EXCLUDES]
    if immutable:
        cmd.insert(3, "--ignore-existing")
    log(f"rclone copy {local.name} -> {target}{' (immutable)' if immutable else ''}")
    return run_stream(cmd, log)


def copy_file(local_file: Path, target: str, log: Log) -> int:
    if not target:
        return 0
    log(f'rclone copyto {local_file.name} -> {target}')
    return run_stream(['rclone', 'copyto', str(local_file), target], log)


def copy_public_text(local: Path, target: str, log: Log, transfers: int = 2) -> int:
    """Refresh public metadata while leaving the downloaded video immutable."""
    if not target:
        return 0
    log(f"rclone public text {local.name} -> {target}")
    return run_stream(["rclone", "copy", str(local), target,
                       "--include", "*/title.txt", "--include", "*/description.txt",
                       "--include", "*/thumbnail.*", "--transfers", str(transfers),
                       "--stats", "60s", "--stats-one-line"], log)


def pull(target: str, local: Path, log: Log, transfers: int = 2) -> int:
    """Copy target -> local without deleting anything locally."""
    if not target:
        log("no Drive folder configured; skipping pull")
        return 0
    log(f"rclone copy {target} -> {local.name}")
    return run_stream(["rclone", "copy", target, str(local),
                       "--transfers", str(transfers), "--checkers", "8",
                       "--stats", "60s", "--stats-one-line"], log)


def folder_present(target: str, local: Path, log: Log) -> bool:
    """True when every file in local exists on target with identical size and hash."""
    sizes = subprocess.run(["rclone", "check", str(local), target],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if sizes.returncode == 0:
        return True
    log(f"verify failed for {local.name}: {(sizes.stdout or sizes.stderr).strip()[:200]}")
    return False


def total_size(target: str) -> str:
    result = subprocess.run(["rclone", "size", target, "--json"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return "unknown"
    try:
        import json

        data = json.loads(result.stdout)
        from common import human_size

        return human_size(float(data.get("bytes", 0)))
    except Exception:
        return "unknown"
