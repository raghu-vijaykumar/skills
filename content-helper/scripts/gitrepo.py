"""Git-tracked source: commit history snapshots to Drive, restore, and prune locals."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from common import Log, human_size, read_json, run_stream, write_json

GITIGNORE = """\
# Track video source, public title/description, and thumbnail beside each backup.
node_modules/
analytics/
.staging/
.snapshots/
analysis/
tmp/
archive.txt
backup-report.json
*.part
/shorts/*/video.mp4
/shorts/*/video.mov
/shorts/*/video.mkv
/shorts/*/video.webm
/long/*/video.mp4
/long/*/video.mov
/long/*/video.mkv
/long/*/video.webm
/drafts/*/video.mp4
/drafts/*/video.mov
/drafts/*/video.mkv
/drafts/*/video.webm
/shorts/*/metadata.json
/long/*/metadata.json
**/assets/generated/
**/assets/sources/**/images/
**/assets/sources/**/videos/
**/assets/sources/**/screenshots/
/drafts/*/original-videos/
"""

TREE_EXCLUDES = ["--exclude", ".git/**", "--exclude", ".snapshots/**",
                 "--exclude", "node_modules/**", "--exclude", "analytics/**",
                 "--exclude", ".staging/**", "--exclude", "tmp/**",
                 "--exclude", "**/assets/generated/**", "--exclude", "**/assets/sources/**/images/**",
                 "--exclude", "**/assets/sources/**/videos/**",
                 "--exclude", "shorts/*/video.mp4", "shorts/*/video.mov", "shorts/*/video.mkv", "shorts/*/video.webm", "--exclude", "long/*/video.mp4", "long/*/video.mov", "long/*/video.mkv", "long/*/video.webm",
                 "--exclude", "drafts/*/video.mp4", "drafts/*/video.mov", "drafts/*/video.mkv", "drafts/*/video.webm", "--exclude", "drafts/*/original-videos/**",
                 "--exclude", "shorts/*/metadata.json", "--exclude", "long/*/metadata.json",
                 "--exclude", "archive.txt", "--exclude", "backup-report.json"]


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def repo_root(path: Path) -> Path | None:
    result = git(path, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def has_remote(root: Path) -> bool:
    return git(root, "remote", "get-url", "origin").returncode == 0


def commit_paths(root: Path, paths: list[Path], log: Log, message: str) -> int:
    """Commit only this backup's paths, then verify its configured Git remote."""
    repo = repo_root(root)
    if repo is None or repo.resolve() != root.resolve() or not has_remote(root):
        log("backup source not pushed: channel Git remote is unavailable")
        return 1
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        log("backup source not pushed: unrelated staged changes are present")
        return 1
    unique = sorted({str(path.resolve().relative_to(root.resolve())) for path in paths})
    staged = git(root, "add", "-A", "--", *unique)
    if staged.returncode != 0:
        log(f"git add failed: {staged.stderr.strip()[:200]}")
        return 1
    if git(root, "diff", "--cached", "--check").returncode != 0:
        log("backup source not pushed: staged whitespace check failed")
        return 1
    if not git(root, "diff", "--cached", "--name-only").stdout.strip():
        return 0
    committed = git(root, "commit", "-m", message)
    if committed.returncode != 0:
        log(f"git commit failed: {committed.stderr.strip()[:200]}")
        return 1
    branch = git(root, "branch", "--show-current").stdout.strip()
    pushed = git(root, "push", "origin", f"HEAD:{branch}")
    if pushed.returncode != 0:
        log(f"local backup commit retained; git push failed: {pushed.stderr.strip()[:200]}")
        return 1
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    remote = git(root, "ls-remote", "origin", f"refs/heads/{branch}").stdout.split("\t")[0]
    if head != remote:
        log("Git push returned but remote HEAD did not match")
        return 1
    log(f"Git backup verified at {head[:12]}")
    return 0


def bundle_dir(root: Path) -> Path:
    return root / ".snapshots"


def ledger_path(root: Path) -> Path:
    return bundle_dir(root) / "index.json"


def init(root: Path, log: Log) -> int:
    root.mkdir(parents=True, exist_ok=True)
    if not (root / ".git").exists():
        result = git(root, "init", "-b", "main")
        if result.returncode != 0:
            log(f"git init failed: {result.stderr.strip()}")
            return 1
        log(f"initialised a git repo at {root}")
    ignore = root / ".gitignore"
    if not ignore.exists():
        ignore.write_text(GITIGNORE, encoding="utf-8")
        log("wrote .gitignore (source and thumbnails tracked; generated media stays out of Git)")
    else:
        log(".gitignore already present; not touched")
    log("next: git add -A && git commit -m 'initial'")
    return 0


def status(root: Path, log: Log) -> int:
    repo = repo_root(root)
    if not repo:
        log(f"{root} is not a git repo; run: content.py code init")
        return 1
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    dirty = [line for line in git(repo, "status", "--porcelain").stdout.splitlines() if line]
    tracked = [p for p in git(repo, "ls-files").stdout.splitlines() if p]
    size = sum((repo / p).stat().st_size for p in tracked if (repo / p).exists())
    snapshots = sorted(bundle_dir(repo).glob("*.bundle"))
    log(f"repo {repo} branch {branch}")
    log(f"tracked {len(tracked)} files, {human_size(size)}; dirty {len(dirty)}")
    log(f"local snapshots {len(snapshots)}")
    for line in dirty[:10]:
        log(f"  {line}")
    return 0


def snapshot(root: Path, drive_folder: str, log: Log, message: str = "",
             allow_dirty: bool = False) -> int:
    repo = repo_root(root)
    if not repo:
        log(f"{root} is not a git repo; run: content.py code init")
        return 1
    dirty = [line for line in git(repo, "status", "--porcelain").stdout.splitlines() if line]
    if dirty and not allow_dirty:
        log(f"{len(dirty)} uncommitted change(s); commit first so the snapshot contains them")
        for line in dirty[:10]:
            log(f"  {line}")
        return 1
    if dirty:
        log(f"warning: {len(dirty)} uncommitted change(s) are NOT in this snapshot")
    head = git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    if not head:
        log("no commits yet; nothing to snapshot")
        return 1

    bundle_dir(repo).mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"{stamp}-{head}.bundle"
    bundle = bundle_dir(repo) / name
    created = git(repo, "bundle", "create", str(bundle), "--all")
    if created.returncode != 0:
        log(f"git bundle failed: {created.stderr.strip()}")
        return 1

    rc = 0
    if drive_folder:
        from drive import copy_file

        rc |= copy_file(bundle, f"{drive_folder.rstrip('/')}/code/snapshots/{name}", log)
        log("mirroring the tracked tree to Drive")
        rc |= run_stream(
            ["rclone", "copy", str(repo), f"{drive_folder.rstrip('/')}/code/tree",
             "--transfers", "4", "--stats", "0", *TREE_EXCLUDES], log)
    else:
        log("no driveFolder configured; snapshot kept locally only")

    ledger = read_json(ledger_path(repo))
    entries = ledger.get("snapshots", [])
    entries.append({"name": name, "head": head, "message": message,
                    "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "drive": f"{drive_folder.rstrip('/')}/code/snapshots/{name}"})
    write_json(ledger_path(repo), {"snapshots": entries})
    log(f"snapshot {name} ({human_size(bundle.stat().st_size)}) rc={rc}")
    return rc


def restore(drive_folder: str, dest: Path, log: Log, name: str | None = None) -> int:
    if not drive_folder:
        log("no driveFolder configured")
        return 1
    source = f"{drive_folder.rstrip('/')}/code/snapshots"
    listing = subprocess.run(["rclone", "lsf", source, "--files-only"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    bundles = sorted(line.strip() for line in listing.stdout.splitlines() if line.strip().endswith(".bundle"))
    if not bundles:
        log(f"no snapshots on Drive at {source}")
        return 1
    chosen = name or bundles[-1]
    temp = Path(tempfile.mkdtemp(prefix="content-helper-restore-"))
    rc = subprocess.run(["rclone", "copyto", f"{source}/{chosen}", str(temp / chosen)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if rc.returncode != 0:
        log(f"download failed: {rc.stderr.strip()[:200]}")
        return 1
    if dest.exists() and any(dest.iterdir()):
        log(f"{dest} is not empty; refusing to clone over it")
        return 1
    clone = subprocess.run(["git", "clone", str(temp / chosen), str(dest)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    shutil.rmtree(temp, ignore_errors=True)
    if clone.returncode != 0:
        log(f"clone failed: {clone.stderr.strip()[:200]}")
        return 1
    log(f"restored {chosen} into {dest}")
    return 0


def prune(root: Path, drive_folder: str, keep: int, log: Log, dry_run: bool = False) -> int:
    repo = repo_root(root)
    if not repo:
        log(f"{root} is not a git repo")
        return 1
    if not drive_folder and not dry_run:
        log("no driveFolder configured; refusing to delete snapshots that are not backed up")
        return 1
    bundles = sorted(bundle_dir(repo).glob("*.bundle"))
    old = bundles[:max(0, len(bundles) - keep)]
    if not old:
        log(f"nothing to prune ({len(bundles)} local snapshot(s), keeping {keep})")
        return 0
    rc = 0
    freed = 0
    for bundle in old:
        target = f"{drive_folder.rstrip('/')}/code/snapshots/{bundle.name}"
        if dry_run:
            log(f"would delete {bundle.name} after checking {target}")
            continue
        listed = subprocess.run(["rclone", "lsjson", target],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if listed.returncode != 0:
            log(f"kept {bundle.name}: not found on Drive")
            rc = 1
            continue
        try:
            remote_size = json.loads(listed.stdout).get("Size", -1)
        except json.JSONDecodeError:
            remote_size = -1
        if remote_size != bundle.stat().st_size:
            log(f"kept {bundle.name}: Drive size {remote_size} != local {bundle.stat().st_size}")
            rc = 1
            continue
        freed += bundle.stat().st_size
        bundle.unlink()
        log(f"deleted local snapshot {bundle.name}")
    log(f"pruned {len(old) if not dry_run else len(old)} local snapshot(s), freed {human_size(freed)}; "
        f"Drive untouched")
    return rc
