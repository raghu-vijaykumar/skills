#!/usr/bin/env python3
"""Apply the Glitch reveal transition at point cues on one master."""
from transitions import run_fixed_transition

TRANSITION_ID = "glitch-reveal"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
