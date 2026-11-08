#!/usr/bin/env python3
"""Operation-specific entrypoint: bounded reflection comparison preview."""
import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from dispatch import run_python  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_python(
        __file__, "edit/clip-edit/scripts/reflection.py", ("preview",), ()))
