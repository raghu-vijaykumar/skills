#!/usr/bin/env python3
"""Join ordered clips with the Zoom in transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "zoom-in"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
