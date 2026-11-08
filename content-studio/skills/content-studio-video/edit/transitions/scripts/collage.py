#!/usr/bin/env python3
"""Catalog-only Collage transition; running this reports that no renderer is bundled."""
from transitions import run_fixed_transition

TRANSITION_ID = "collage"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
