#!/usr/bin/env python3
"""Operation-specific entrypoint for a maintained Content Studio backend."""
import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from dispatch import run_python  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_python(__file__, "edit/autocut/scripts/reframe.py", ("--mode", "subjects"), ()))
