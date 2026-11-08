#!/usr/bin/env python3
"""Join ordered clips with the Wipe left transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "wipe-left"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
