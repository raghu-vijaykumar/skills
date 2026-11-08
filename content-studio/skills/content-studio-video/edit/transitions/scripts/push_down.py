#!/usr/bin/env python3
"""Join ordered clips with the Push down transition."""
from transitions import run_fixed_transition

TRANSITION_ID = "push-down"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
