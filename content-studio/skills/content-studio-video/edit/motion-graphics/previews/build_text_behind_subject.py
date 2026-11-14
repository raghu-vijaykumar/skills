"""Rebuild the synthetic rising-title GIF from an actual timeline preview."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

FOLDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FOLDER.parent.parent / "timeline" / "scripts"))
import compiler  # noqa: E402
import model  # noqa: E402


def main() -> None:
    output = Path(__file__).with_name("text-behind-subject.gif")
    with tempfile.TemporaryDirectory(prefix="behind-subject-preview-") as scratch:
        root = Path(scratch)
        size = (270, 480)
        scene = Image.new("RGB", size, "#8DC9F0")
        draw = ImageDraw.Draw(scene)
        draw.ellipse((218, 15, 258, 55), fill="#FFF2CB")
        draw.polygon([(0, 270), (70, 185), (125, 250), (210, 170),
                      (270, 245), (270, 480), (0, 480)], fill="#365B6A")
        draw.polygon([(0, 340), (80, 290), (155, 318), (270, 265),
                      (270, 480), (0, 480)], fill="#52775A")
        draw.ellipse((117, 260, 151, 294), fill="#252F3F")
        draw.polygon([(112, 292), (155, 292), (167, 414), (99, 414)],
                     fill="#B46D48")
        draw.line([(113, 310), (73, 264)], fill="#B46D48", width=17)
        draw.line([(153, 310), (190, 258)], fill="#B46D48", width=17)
        scene_path = root / "scene.png"
        scene.save(scene_path)
        matte = Image.new("L", size, 0)
        mask = ImageDraw.Draw(matte)
        mask.polygon([(0, 270), (70, 185), (125, 250), (210, 170),
                      (270, 245), (270, 480), (0, 480)], fill=255)
        mask.ellipse((117, 260, 151, 294), fill=255)
        mask.polygon([(112, 292), (155, 292), (167, 414), (99, 414)], fill=255)
        mask.line([(113, 310), (73, 264)], fill=255, width=17)
        mask.line([(153, 310), (190, 258)], fill=255, width=17)
        matte_path = root / "matte.png"
        matte.save(matte_path)
        source = root / "scene.mp4"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-framerate", "10", "-i", str(scene_path),
            "-f", "lavfi", "-i", "sine=frequency=330:duration=3",
            "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(source)], check=True, capture_output=True)
        plan_dir = root / "preflight"
        plan_dir.mkdir()
        plan = plan_dir / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render",
                                    "steps": [{"id": "synthetic-fixture"}]}))
        plan_hash = model.sha256_file(plan)
        (plan_dir / "approval.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "review_note": "synthetic test fixture"}))
        (plan_dir / "checklist.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "items": [{"id": "synthetic-fixture"}]}))
        font = root / "font.ttf"
        shutil.copyfile(Path("C:/Windows/Fonts/arialbd.ttf"), font)
        timeline = model.make_initial(plan, source, root / "unused.mp4",
                                      fps=10, width=270, height=480)
        timeline["picture"][0]["source_out"] = 3
        timeline["operations"] = [{
            "id": "demo", "method": "text-behind-subject", "text": "ITALY",
            "start": 0, "end": 3, "rise_seconds": 1.5,
            "from_y": .66, "to_y": .13, "font_height": .16,
            "font_source": font.name, "font_sha256": model.sha256_file(font),
            "matte_source": matte_path.name,
            "matte_sha256": model.sha256_file(matte_path),
            "review_status": "pending_review"}]
        preview = root / "preview.mp4"
        compiler.preview(timeline, model.validate(timeline, require_review=False),
                         preview, 0, 3)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(preview), "-vf", "fps=10,scale=270:-1:flags=lanczos",
            str(output)], check=True, capture_output=True)
    print(output)


if __name__ == "__main__":
    main()
