#!/usr/bin/env python3
"""Audit and normalize channel style identity across a scene plan and timeline."""
import argparse
import copy
import json
from pathlib import Path

PROFILES = {
    "travel-vlog": {
        "palette": ["#F6C16B", "#163F50", "#FFFFFF"],
        "font_family": "Noto Sans", "caption_position": "top",
        "safe_margin_percent": 7, "transition": "soft-cut",
        "motion_intensity": "medium", "look": "clean-natural",
        "audio_target_lufs": -14, "max_styles_per_video": 3,
    },
    "technical-explainer": {
        "palette": ["#58C5F7", "#101C30", "#FFFFFF"],
        "font_family": "Noto Sans", "caption_position": "top",
        "safe_margin_percent": 8, "transition": "match-cut",
        "motion_intensity": "medium", "look": "cool-cinematic",
        "audio_target_lufs": -14, "max_styles_per_video": 2,
    },
    "daily-vlog": {
        "palette": ["#E6BA88", "#252525", "#FFFFFF"],
        "font_family": "Noto Sans", "caption_position": "bottom",
        "safe_margin_percent": 8, "transition": "straight-cut",
        "motion_intensity": "low", "look": "clean-natural",
        "audio_target_lufs": -14, "max_styles_per_video": 3,
    },
}

IDENTITY_FIELDS = ("palette", "font_family", "caption_position", "safe_margin_percent",
                   "audio_target_lufs")
PRESENTATION_FIELDS = IDENTITY_FIELDS + ("transition", "motion_intensity", "look")

def profile_for(name, overrides=None):
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    result = copy.deepcopy(PROFILES[name])
    for key, value in (overrides or {}).items():
        if key not in result:
            raise ValueError(f"Unknown profile setting: {key}")
        result[key] = value
    if not isinstance(result["palette"], list) or len(result["palette"]) < 2:
        raise ValueError("Profile palette must contain at least two colors")
    if not 0 <= float(result["safe_margin_percent"]) <= 25:
        raise ValueError("Invalid safe margin")
    return result

def audit(data, profile):
    findings = []
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        raise ValueError("Scenes must be a list")
    styles = {s.get("style") for s in scenes if s.get("style")}
    if len(styles) > int(profile["max_styles_per_video"]):
        findings.append({"severity": "review", "scope": "video", "field": "style",
                         "message": "Too many visual styles for this profile",
                         "actual": sorted(styles)})
    for i, scene in enumerate(scenes):
        for key in PRESENTATION_FIELDS:
            if key in scene and scene[key] != profile[key]:
                findings.append({"severity": "review" if key in IDENTITY_FIELDS else "info",
                                 "scope": scene.get("id", str(i)), "field": key,
                                 "expected": profile[key], "actual": scene[key]})
    return {"profile": profile, "scene_count": len(scenes), "findings": findings,
            "review_required": any(f["severity"] == "review" for f in findings)}

def normalize(data, profile):
    result = copy.deepcopy(data)
    for scene in result.get("scenes", []):
        scene.setdefault("presentation", {})
        for key in PRESENTATION_FIELDS:
            # Identity is consistent, while explicitly chosen editorial treatment
            # can vary by scene and is surfaced for review in the audit.
            if key in IDENTITY_FIELDS:
                scene["presentation"][key] = copy.deepcopy(profile[key])
            else:
                scene["presentation"].setdefault(key, copy.deepcopy(profile[key]))
    result["style_profile"] = copy.deepcopy(profile)
    return result

def annotate_timeline(data, profile):
    result = copy.deepcopy(data)
    result["style_profile"] = copy.deepcopy(profile)
    for track in result.get("tracks", []):
        if track.get("kind") != "video":
            continue
        for clip in track.get("clips", []):
            clip.setdefault("style", {})
            for key in PRESENTATION_FIELDS:
                clip["style"].setdefault(key, copy.deepcopy(profile[key]))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--kind", choices=["scenes", "timeline"], default="scenes")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    overrides = json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides else {}
    profile = profile_for(args.profile, overrides)
    report = audit(data, profile) if args.kind == "scenes" else {
        "profile": profile, "clip_count": sum(len(t.get("clips", [])) for t in data.get("tracks", []) if t.get("kind") == "video"),
        "review_required": True, "findings": []}
    output = normalize(data, profile) if args.kind == "scenes" else annotate_timeline(data, profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "review_required": report["review_required"], "findings": len(report["findings"])}))

if __name__ == "__main__":
    main()
