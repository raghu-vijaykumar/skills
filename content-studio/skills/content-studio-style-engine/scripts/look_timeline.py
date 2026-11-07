"""Non-destructive Content Studio timeline look annotations and FFmpeg graph."""
import json
import math
from pathlib import Path

def load_looks(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["ranges"] if isinstance(data, dict) else data

def validate_looks(looks, presets, root=None):
    ordered = sorted(looks, key=lambda x: float(x["start"]))
    last = 0.0
    for look in ordered:
        start, end = float(look["start"]), float(look["end"])
        fade = float(look.get("fade", 0.35))
        if not all(math.isfinite(v) for v in (start, end, fade)) or start < last or end <= start or fade < 0 or fade * 2 > end - start:
            raise ValueError("Invalid, overlapping, or too-short look range")
        if bool(look.get("preset")) == bool(look.get("lut")):
            raise ValueError("Exactly one of preset or lut required")
        if look.get("preset") and look["preset"] not in presets:
            raise ValueError("Unknown preset")
        if look.get("lut"):
            path = Path(look["lut"])
            if root and not path.is_absolute():
                path = Path(root) / path
            path = path.resolve()
            if path.suffix.lower() != ".cube" or not path.is_file():
                raise ValueError("LUT must reference an existing .cube file")
            look["_lut_path"] = str(path)
        last = end
    return ordered

def graph(looks, presets, root=None):
    ordered = validate_looks([dict(x) for x in looks], presets, root)
    parts = ["[0:v:0]format=yuv444p[v0]"]
    current = "v0"
    for index, look in enumerate(ordered):
        source, graded, output = f"base{index}", f"grade{index}", f"v{index+1}"
        parts.append(f"[{current}]split=2[{source}][input{index}]")
        if "preset" in look:
            p = presets[look["preset"]]
            grade = "eq=" + ":".join(f"{key}={p[key]}" for key in ("contrast", "brightness", "saturation", "gamma"))
        else:
            path = look["_lut_path"].replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            grade = f"lut3d=file='{path}'"
        parts.append(f"[input{index}]{grade}[{graded}]")
        start, end, fade = float(look["start"]), float(look["end"]), float(look.get("fade", 0.35))
        if fade == 0:
            alpha = f"between(T,{start},{end})"
        else:
            alpha = f"max(0,min(1,(T-{start})/{fade},({end}-T)/{fade}))"
        # blend expression uses T (frame timestamp) and pixel A/B.
        parts.append(f"[{source}][{graded}]blend=all_expr='A*(1-({alpha}))+B*({alpha})'[{output}]")
        current = output
    parts.append(f"[{current}]format=yuv420p[vout]")
    return ";".join(parts)

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
