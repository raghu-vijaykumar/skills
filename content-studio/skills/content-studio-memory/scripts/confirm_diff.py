#!/usr/bin/env python3
# Compatibility dispatch to the migrated Content Studio implementation.
import runpy
import sys
from pathlib import Path

_target = (Path(__file__).resolve().parent / '../../content-studio-video/memory/scripts/confirm_diff.py').resolve()
sys.path.insert(0, str(_target.parent))
globals().update(runpy.run_path(str(_target), run_name=__name__))
