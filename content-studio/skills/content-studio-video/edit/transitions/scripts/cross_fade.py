#!/usr/bin/env python3
"""Join ordered clips with the Cross fade transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "cross-fade"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
