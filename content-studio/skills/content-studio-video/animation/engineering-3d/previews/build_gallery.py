"""Render the synthetic Blender cutaway gallery without a production draft."""

import argparse
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[6]


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr)[-1200:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", default="blender", help="Blender 4.x executable")
    args = parser.parse_args()
    work = REPO / "tmp/capability-gallery/engineering-3d"
    work.mkdir(parents=True, exist_ok=True)
    spec = json.loads((SKILL / "examples/illustrative-cpu-assembly.json")
                      .read_text(encoding="utf-8"))
    # A small preview preserves all authored events while avoiding a full
    # delivery-resolution render for documentation evidence.
    spec.update({"width": 640, "height": 360, "fps": 12})
    scene = work / "illustrative-cpu-small.json"
    scene.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    video = work / "illustrative-cpu.mp4"
    run([args.blender, "-b", "--factory-startup", "-t", "4", "--python",
         str(SKILL / "scripts/engineering_blender.py"), "--", str(scene),
         str(video)])
    target = SKILL / "previews/illustrative-cpu.gif"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-filter_complex", "fps=8,scale=480:-1:flags=lanczos,split[a][b];"
         "[b]palettegen=stats_mode=diff[p];"
         "[a][p]paletteuse=dither=bayer:bayer_scale=3", str(target)])
    print(f"Rendered {target} from {video}")


if __name__ == "__main__":
    main()
