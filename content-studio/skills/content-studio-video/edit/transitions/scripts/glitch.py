#!/usr/bin/env python3
"""Apply the Glitch transition at point cues on one master."""
from transitions import run_fixed_transition

TRANSITION_ID = "glitch"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
