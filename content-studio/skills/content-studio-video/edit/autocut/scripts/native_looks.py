"""Approved creative looks as FFmpeg filter-graph stages for canonical timeline."""
from pathlib import Path

LOOKS = {
    "warm-golden": (1.06,.015,1.16,1.04),
    "cool-cinematic": (1.13,-.015,.82,.97),
    "vintage-fade": (.88,.035,.72,1.08),
    "vibrant-travel": (1.08,.01,1.3,1.02),
    "soft-portrait": (.95,.02,.94,1.05),
    "mono-noir": (1.22,-.025,0,.94),
    "clean-natural": (1.02,0,1.04,1),
}

def apply(clip, root, label="[0:v:0]"):
    items = [e for e in clip.get("enhancements", [])
             if e.get("stage") == "creative_look" and e.get("review_status") in ("approved", "auto_approved")]
    graph = []
    for i, e in enumerate(items):
        start = max(0., float(e["source_start"]) - float(clip["source_in"]))
        end = min(float(clip["duration"]), float(e["source_end"]) - float(clip["source_in"]))
        if end <= start:
            continue
        fade = float(e.get("fade", .35))
        if fade < 0 or 2*fade > end-start:
            raise ValueError("Invalid fade")
        if bool(e.get("lut")) == bool(e.get("preset")):
            raise ValueError("Specify either preset or LUT")
        if e.get("lut"):
            file = (Path(root)/e["lut"]).resolve()
            if not file.is_relative_to(Path(root).resolve()) or not file.is_file() or file.suffix.lower() != ".cube":
                raise ValueError("Unsafe LUT path")
            escaped = file.as_posix().replace(":", "\\:").replace("'", "\\'")
            grade = "lut3d=file='" + escaped + "'"
        else:
            if e["preset"] not in LOOKS:
                raise ValueError("Unknown preset")
            c,b,s,g = LOOKS[e["preset"]]
            grade = f"eq=contrast={c}:brightness={b}:saturation={s}:gamma={g}"
        a, b, c = f"original{i}", f"candidate{i}", f"graded{i}"
        out = f"look{i}"
        graph += [f"{label}format=yuv444p,split=2[{a}][{b}]", f"[{b}]{grade}[{c}]"]
        alpha = (f"between(T,{start},{end})" if fade == 0 else
                 f"max(0,min(1,(T-{start})/{fade},({end}-T)/{fade}))")
        graph.append(f"[{a}][{c}]blend=all_expr='A*(1-({alpha}))+B*({alpha})'[{out}]")
        label = f"[{out}]"
    return graph, label
