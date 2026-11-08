#!/usr/bin/env python3
"""Catalog-only Zoom out transition; running this reports that no renderer is bundled."""
from transitions import run_fixed_transition

TRANSITION_ID = "zoom-out"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
