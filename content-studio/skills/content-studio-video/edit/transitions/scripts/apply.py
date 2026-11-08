#!/usr/bin/env python3
"""Apply reviewed, time-preserving point transitions to one finished video."""

import sys
from transitions import main

if __name__ == "__main__":
    # Fix the operation so a direct skill call cannot become a clip join.
    raise SystemExit(main(["apply", *sys.argv[1:]]))
