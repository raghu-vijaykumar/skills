"""Shared config, logging and process helpers for content-helper."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_ROOT / "config.json"
LOCAL_OVERRIDE = SKILL_ROOT / "config.local.json"
DEFAULT_WORKSPACE = Path.home() / "content"


def channel_path(root: Path, name: str) -> Path:
    """Keep older channels' paths while compact workspaces use analysis/."""
    compact = {"analytics": "analytics", ".staging": ".staging",
               ".snapshots": ".snapshots", "tmp/source-assets": "source-assets"}
    analysis = root / "analysis"
    return analysis / compact[name] if analysis.is_dir() else root / name

ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Log:
    def __init__(self, path: Path | None = None):
        self.path = path
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str) -> None:
        line = f"[{now()}] {msg}"
        print(line, flush=True)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


def sanitize(text: str, max_len: int = 90) -> str:
    text = re.sub(r"\s+", " ", ILLEGAL.sub("", text)).strip().rstrip(".")
    if len(text) > max_len:
        cut = text[:max_len]
        space = cut.rfind(" ")
        text = (cut[:space] if space > max_len * 0.6 else cut).rstrip(" -|,")
    return text or "untitled"


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024 or unit == "TB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{int(num)} B"
        num /= 1024
    return f"{num:.1f} TB"


def config_template() -> dict:
    return {
        "workspace": str(DEFAULT_WORKSPACE),
        "remoteRoot": "gdrive:Content",
        "browser": "brave",
        "browserDebugPort": 9223,
        "quality": "best",
        "transfers": 2,
        "includePrivate": True,
        "channels": {
            "example-channel": {
                "name": "My Channel",
                "url": "https://www.youtube.com/@some-handle",
                "driveFolder": "gdrive:Content/example-channel",
                "includePrivate": True,
                "intro": "assets/intro.mp4",
            }
        },
    }


def merge_dict(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key == "channels" and isinstance(value, dict) and isinstance(base.get(key), dict):
            for slug, channel in value.items():
                if isinstance(channel, dict) and isinstance(base[key].get(slug), dict):
                    base[key][slug] = merge_dict(base[key][slug], channel)
                else:
                    base[key][slug] = channel
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: Path | None = None) -> dict:
    path = Path(path or DEFAULT_CONFIG).expanduser()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config_template(), indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"Created a config template at {path}\nEdit it, then run again.")
    with path.open(encoding="utf-8-sig") as fh:
        cfg = json.load(fh)
    if path.resolve() == DEFAULT_CONFIG.resolve() and LOCAL_OVERRIDE.exists():
        with LOCAL_OVERRIDE.open(encoding="utf-8-sig") as fh:
            cfg = merge_dict(cfg, json.load(fh))
    cfg.setdefault("workspace", str(DEFAULT_WORKSPACE))
    cfg.setdefault("quality", "best")
    cfg.setdefault("transfers", 2)
    cfg.setdefault("browser", "brave")
    cfg.setdefault("browserDebugPort", 9223)
    cfg.setdefault("includePrivate", True)
    cfg.setdefault("channels", {})
    return cfg


def channel_settings(cfg: dict, slug: str, channel: dict) -> dict:
    source = channel.get("url") or channel.get("channelId") or channel.get("handle")
    if not source:
        raise SystemExit(f"channel '{slug}' needs a url, handle or channelId")
    remote_root = str(cfg.get("remoteRoot") or "").rstrip("/")
    name = channel.get("name") or slug
    return {
        "slug": slug,
        "source": source,
        "channel_id": channel.get("channelId", ""),
        "name": name,
        "quality": channel.get("quality", cfg.get("quality")),
        "include_private": bool(channel.get("includePrivate",
                                            channel.get("includeScheduled",
                                                        cfg.get("includePrivate", True)))),
        "drive_folder": channel.get("driveFolder")
        or (f"{remote_root}/{slug}" if remote_root else ""),
        "intro": channel.get("intro", "assets/intro.mp4"),
        "analytics": channel.get("analytics", {}),
        "browser": channel.get("browser") or cfg.get("browser", "brave"),
        "raw": channel,
    }


def select_channels(cfg: dict, name: str | None) -> list[tuple[str, dict]]:
    channels = cfg.get("channels", {})
    if name:
        if name not in channels:
            raise SystemExit(f"unknown channel '{name}'; try --list")
        return [(name, channels[name])]
    return list(channels.items())


def channel_root(cfg: dict, slug: str) -> Path:
    return Path(cfg["workspace"]).expanduser() / slug


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path)


def run_stream(cmd: list[str], log: Log, echo: tuple[str, ...] = ()) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", bufsize=1)
    last_bucket = -1
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip()
        if not line:
            continue
        match = re.search(r"\[download\]\s+(\d{1,3}(?:\.\d)?)%", line)
        if match:
            bucket = int(float(match.group(1))) // 10
            if bucket != last_bucket:
                log(line)
                last_bucket = bucket
            continue
        if "Destination" in line or "ERROR" in line or "WARNING" in line \
                or "Copied (new)" in line or "Transferred" in line:
            log(line)
        elif any(token in line for token in echo):
            log(line)
    code = proc.wait()
    return code if code >= 0 else 1


def which_tool(name: str) -> bool:
    from shutil import which

    return bool(which(name))


def archive_ids(archive: Path) -> set[str]:
    if not archive.exists():
        return set()
    ids = set()
    for line in archive.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            ids.add(parts[1])
    return ids


def read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8-sig") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
