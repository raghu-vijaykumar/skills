#!/usr/bin/env python3
"""Join ordered clips with the Horizontal banding transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "horizontal-banding"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
