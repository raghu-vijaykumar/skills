#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical stock-library CTA generator."""

from pathlib import Path
import sys

# Existing approved commands keep working while design ownership moves to stock-library.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "stock-library" / "scripts"))
from cta import POSITIONS, VARIANTS, draw_frame, main, render, states  # noqa: E402


if __name__ == "__main__":
    main()
