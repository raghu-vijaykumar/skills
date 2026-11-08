#!/usr/bin/env python3
"""Join explicitly ordered clips with reviewed boundary transitions."""

import sys
from transitions import main

if __name__ == "__main__":
    # Join changes total duration; it is a distinct approved method.
    raise SystemExit(main(["join", *sys.argv[1:]]))
