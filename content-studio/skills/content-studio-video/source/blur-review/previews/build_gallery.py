"""Show blur review evidence without approving or applying any cuts."""

import csv
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
REPO = Path(__file__).resolve().parents[6]
WORK = REPO / "tmp/capability-gallery/blur-review"
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "edit/clip-edit/scripts"))
sys.path.insert(0, str(ROOT / "shared"))
import preprocess  # noqa: E402
from preview_gif import write_comparison  # noqa: E402


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-800:])


def range_clip(source, time, path):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", str(time), "-i", str(source), "-t", "0.75", "-an",
         "-c:v", "libx264", str(path)])


def main():
    source = WORK / "synthetic-blur.mp4"
    # The severe blur is introduced only in this temporary test source.
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=3",
         "-vf", "gblur=sigma=12:enable='between(t,1,1.75)'",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)])
    analysis = WORK / "analysis"
    analysis.mkdir(exist_ok=True)
    report = {}
    preprocess.write_review(source, {"index": 0, "width": 320, "height": 180},
                            3, analysis, report, auto_remove=False, images=True)
    rows = list(csv.DictReader((analysis / "review.csv").open(encoding="utf-8")))
    if not rows or any(row["remove"] for row in rows):
        raise RuntimeError("Expected unapproved synthetic blur candidates")
    candidate = next((row for row in rows if float(row["start"]) <= 1.4
                      <= float(row["end"])), rows[0])
    clear = WORK / "clear-range.mp4"
    blurred = WORK / "flagged-range.mp4"
    range_clip(source, .2, clear)
    range_clip(source, float(candidate["start"]), blurred)
    # This compares two source ranges only; it does not render or approve a cut.
    write_comparison([clear, blurred],
                     ["CLEAR SOURCE RANGE", "FLAGGED BLUR - NO CUT"],
                     SKILL / "previews/blur-candidate.gif", duration=.75, fps=8)
    # Keep the exact scanner rows as evidence, but do not mark remove=yes.
    (SKILL / "previews/scan-review.csv").write_bytes(
        (analysis / "review.csv").read_bytes())
    print(f"{len(rows)} unapproved candidate(s); example={candidate['start']}-{candidate['end']}s")


if __name__ == "__main__":
    main()
