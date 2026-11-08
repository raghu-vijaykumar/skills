#!/usr/bin/env python3
"""Apply the Fade through white transition at a point or across a clip join."""
from transitions import run_fixed_transition

TRANSITION_ID = "fade-through-white"

if __name__ == "__main__":
    raise SystemExit(run_fixed_transition(TRANSITION_ID))
