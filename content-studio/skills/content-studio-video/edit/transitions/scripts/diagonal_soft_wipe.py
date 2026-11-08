#!/usr/bin/env python3
"""Join ordered clips with the Diagonal soft wipe transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "diagonal-soft-wipe"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
