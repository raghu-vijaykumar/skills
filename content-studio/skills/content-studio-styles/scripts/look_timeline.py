"""Non-destructive Content Studio timeline look annotations.

Look *choice* lives here: which preset or LUT applies to which timeline range.
Filter graph construction and rendering live in ``content-studio-videoedit``.
"""
import json
import sys
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BUNDLE_ROOT / "skills" / "content-studio-videoedit" / "scripts"))

from filters import validate_looks  # noqa: E402


def load_looks(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return data["ranges"] if isinstance(data, dict) else data


def annotate_timeline(timeline, looks, presets, root=None):
    """Attach editable look effects to each video clip, translating global time to source time."""
    ordered = validate_looks([dict(x) for x in looks], presets, root)
    result = json.loads(json.dumps(timeline))
    for track in result.get("tracks", []):
        if track.get("kind") != "video":
            continue
        for clip in track.get("clips", []):
            clip_start = float(clip.get("start", 0))
            source_in = float(clip["source_in"])
            duration = float(clip.get("duration", float(clip["source_out"]) - source_in))
            annotations = []
            for look in ordered:
                begin = max(clip_start, float(look["start"]))
                finish = min(clip_start + duration, float(look["end"]))
                if finish <= begin:
                    continue
                annotations.append({"stage": "creative_look", "preset": look.get("preset"),
                                    "lut": look.get("lut"), "fade": look.get("fade", 0.35),
                                    "timeline_start": begin, "timeline_end": finish,
                                    "source_start": source_in + begin - clip_start,
                                    "source_end": source_in + finish - clip_start,
                                    "review_status": "review_required"})
            clip.setdefault("enhancements", []).extend(annotations)
    return result
