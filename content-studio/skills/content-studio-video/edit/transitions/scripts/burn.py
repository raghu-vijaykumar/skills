#!/usr/bin/env python3
"""Apply the Burn transition at point cues on one master."""
from transitions import run_fixed_transition

TRANSITION_ID = "burn"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
