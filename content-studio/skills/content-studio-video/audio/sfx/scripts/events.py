#!/usr/bin/env python3
"""Build evidence-linked video events and propose reviewable SFX cues."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("content_studio_sfx", HERE / "sfx.py")
sfx = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(sfx)

ROLES = {
    "click": ("click", "tick"), "toggle": ("snap", "click"),
    "appear": ("pop", "land.light"), "move": ("whoosh.short", "zip"),
    "cut": ("whoosh.short",), "impact": ("hit", "land"),
    "reveal": ("swell", "hit"), "typing": ("key", "key.run"),
    "camera": ("snap", "click"), "error": ("glitch",),
}
STYLE_FAMILIES = {
    "calm": ("ui_pop", "tap", "swish", "knock", "mallet"),
    "crisp": ("pro_click", "pro_pop", "whoosh_fast", "pro_impact", "shutter"),
    "minimal": ("click", "tap", "pop", "swish"),
    "launch": ("ui_pop", "knock", "cut_hit", "reverse_swell", "mallet"),
}


def _sha(path: Path) -> str:
    return sfx.library.digest_file(path)


def _run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-700:])
    return result.stdout + result.stderr


def _probe(video: Path) -> dict:
    return json.loads(_run(["ffprobe", "-v", "error", "-show_streams",
                            "-show_format", "-of", "json", str(video)]))


def _semantic(label: str) -> str:
    text = label.lower()
    for kind, words in (
        ("error", ("error", "glitch", "failure")),
        ("typing", ("type", "keyboard", "character")),
        ("camera", ("shutter", "snapshot", "photo")),
        ("toggle", ("toggle", "switch")),
        ("click", ("click", "press", "button")),
        ("impact", ("hit", "slam", "impact", "land")),
        ("move", ("slide", "swipe", "move", "pan", "fly")),
        ("appear", ("appear", "pop", "enter", "arrive")),
        ("reveal", ("reveal", "unveil", "open")),
    ):
        if any(word in text for word in words):
            return kind
    return "uncertain"


def _audio_samples(path: Path, start: float = 0, duration: float | None = None) -> array:
    """Decode a bounded mono window for Earshot-style bed and take measurements."""
    command = ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}", "-i", str(path)]
    if duration is not None:
        command += ["-t", f"{duration:.4f}"]
    command += ["-ac", "1", "-ar", "48000", "-f", "f32le", "-"]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-700:])
    samples = array("f")
    samples.frombytes(result.stdout)
    return samples


def _window_level(samples: array, loudest: bool) -> float | None:
    """Measure 50 ms windows; a quiet music gap is treated as no bed."""
    width = 2400
    powers = [sum(value * value for value in samples[i:i + width]) / width
              for i in range(0, len(samples) - width + 1, width)]
    if not powers:
        return None
    powers.sort()
    power = powers[-1] if loudest else powers[len(powers) // 2]
    return 10 * math.log10(max(power, 1e-12))


def _music_gain(bed: Path, at: float, effect: Path) -> tuple[float, dict]:
    """Set a proposed SFX take near 6 dB over the measured pre-cue bed."""
    bed_start = max(0.0, at - 1.0)
    bed_db = _window_level(_audio_samples(bed, bed_start, at - bed_start), False)
    take = _audio_samples(effect)
    take_db = _window_level(take, True)
    if bed_db is None or bed_db < -60 or take_db is None:
        return .35, {"bed_db": bed_db, "take_db": take_db, "fallback": True}
    peak = max((abs(value) for value in take), default=0)
    ceiling_gain = .89 / peak if peak else 1.0
    gain = min(1.0, ceiling_gain, 10 ** ((bed_db + 6 - take_db) / 20))
    return round(max(.01, gain), 4), {"bed_db": round(bed_db, 2),
                                     "take_db": round(take_db, 2),
                                     "target_over_bed_db": 6, "fallback": False}


def analyze_remotion(plan: Path) -> dict:
    """Authored frame events are better evidence than guessing from renders."""
    data = json.loads(plan.read_text(encoding="utf-8"))
    fps = data.get("fps")
    if not isinstance(fps, (int, float)) or fps <= 0 or not isinstance(data.get("scenes"), list):
        raise ValueError("Expected an authored scene plan with fps and scenes")
    events = []
    for scene in data["scenes"]:
        for index, state in enumerate(scene.get("stateChanges", [])):
            kind = _semantic(state.get("label", ""))
            frame = state.get("frame")
            if not isinstance(frame, int) or frame < scene["startFrame"] or frame >= scene["endFrame"]:
                raise ValueError(f"Invalid state frame in {scene['id']}")
            events.append({"id": f"{scene['id']}-state-{index}", "time": frame / fps,
                           "event_type": kind, "confidence": .9 if kind != "uncertain" else .4,
                           "audio_context": "narration" if scene.get("narrationCueIds") else "quiet",
                           "evidence": {"scene_id": scene["id"], "frame": frame,
                                        "label": state.get("label", "")}})
    return {"schema_version": 1, "route": "remotion", "source": str(plan.resolve()),
            "source_sha256": _sha(plan), "duration_seconds": data["durationFrames"] / fps,
            "fps": fps, "events": events}


def _silence(video: Path, duration: float, has_audio: bool) -> list[tuple[float, float]]:
    if not has_audio:
        return [(0.0, duration)]
    output = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
                   "-vn", "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", output)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", output)]
    if len(starts) > len(ends):
        ends.append(duration)
    return list(zip(starts, ends))


def _motion_peaks(video: Path, duration: float, cuts: list[float]) -> list[float]:
    """Find coarse action windows from low-resolution frame change, not semantics."""
    command = ["ffmpeg", "-v", "error", "-i", str(video), "-an", "-vf",
               "fps=4,scale=96:54,format=gray", "-f", "rawvideo", "-"]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-700:])
    size = 96 * 54
    frames = [result.stdout[i:i + size] for i in range(0, len(result.stdout), size)]
    diffs = [sum(abs(a - b) for a, b in zip(before, after)) / size
             for before, after in zip(frames, frames[1:]) if len(after) == size]
    if not diffs:
        return []
    ordered = sorted(diffs)
    floor = max(10.0, ordered[len(ordered) // 2] * 1.8)
    candidates = [(index, value) for index, value in enumerate(diffs)
                  if value >= floor and value >= diffs[max(0, index - 1)] and
                  value >= diffs[min(len(diffs) - 1, index + 1)]]
    output = []
    for index, _ in sorted(candidates, key=lambda row: -row[1]):
        at = (index + 1) / 4
        if (.2 < at < duration - .2 and
                all(abs(at - cut) > .35 for cut in cuts) and
                all(abs(at - prior) > .5 for prior in output)):
            output.append(at)
        if len(output) >= 40:
            break
    return sorted(output)


def _frames(video: Path, folder: Path, prefix: str, at: float,
            offsets: tuple[float, ...]) -> list[str]:
    frames = []
    for index, offset in enumerate(offsets):
        frame = folder / f"{prefix}-{index}.jpg"
        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
              "-ss", f"{at + offset:.4f}", "-i", str(video), "-frames:v", "1",
              "-vf", "scale=640:-2", str(frame)])
        frames.append(str(frame))
    return frames


def analyze_edited(video: Path, evidence_dir: Path, threshold: float = .35) -> dict:
    """Find candidate boundaries; a reviewer still identifies visual meaning."""
    if not 0 < threshold < 1:
        raise ValueError("Scene threshold must be between zero and one")
    video = video.resolve()
    info = _probe(video)
    duration = float(info["format"]["duration"])
    has_audio = any(stream["codec_type"] == "audio" for stream in info["streams"])
    scan = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
                 "-vf", f"select=gt(scene\\,{threshold}),showinfo", "-an", "-f", "null", "-"])
    times = sorted({round(float(value), 4) for value in
                    re.findall(r"showinfo[^\n]*pts_time:([\d.]+)", scan)
                    if .15 < float(value) < duration - .15})
    quiet = _silence(video, duration, has_audio)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    events = []
    for index, at in enumerate(times):
        frames = _frames(video, evidence_dir, f"cut-{index:04d}", at, (-.08, .08))
        # Silence is measurable; other audio needs actual listening before placement.
        is_quiet = any(start <= at - .08 and end >= at + .08 for start, end in quiet)
        events.append({"id": f"cut-{index:04d}", "time": at, "event_type": "cut",
                       "confidence": .55, "audio_context": "quiet" if is_quiet else "unknown",
                       "evidence": {"frames": frames, "note": "Boundary candidate; inspect motion and scene meaning"}})
    for index, at in enumerate(_motion_peaks(video, duration, times)):
        frames = _frames(video, evidence_dir, f"motion-{index:04d}", at,
                         (-.16, 0, .16))
        is_quiet = any(start <= at - .16 and end >= at + .16 for start, end in quiet)
        events.append({"id": f"motion-{index:04d}", "time": at,
                       "event_type": "uncertain", "confidence": .45,
                       "audio_context": "quiet" if is_quiet else "unknown",
                       "evidence": {"frames": frames,
                                    "note": "Motion peak; identify action before proposing SFX"}})
    events.sort(key=lambda row: row["time"])
    return {"schema_version": 1, "route": "edited", "source": str(video),
            "source_sha256": _sha(video), "duration_seconds": duration,
            "events": events, "requires_visual_review": True}


def propose(manifest: dict, assets: Path, style: str = "calm",
            mode: str = "preview", music_bed: Path | None = None) -> dict:
    if manifest.get("schema_version") != 1 or manifest.get("route") not in {"edited", "remotion"}:
        raise ValueError("Unsupported event manifest")
    if style not in STYLE_FAMILIES or mode not in {"preview", "delivery"}:
        raise ValueError("Unknown style or proposal mode")
    entries = sfx.library.read_catalogue(assets)
    if music_bed is not None and not music_bed.is_file():
        raise ValueError("Music bed is missing")
    output = []
    previous_end = -.5
    for event in sorted(manifest.get("events", []), key=lambda item: item["time"]):
        kind = event.get("event_type")
        at = float(event.get("time", -1))
        confidence = float(event.get("confidence", 0))
        context = event.get("audio_context")
        if not math.isfinite(at) or not 0 <= at < manifest["duration_seconds"]:
            raise ValueError("Event time is outside the source")
        reason = None
        if kind not in ROLES or confidence < .7:
            reason = "uncertain visible event"
        elif context in {"dialogue", "natural", "unknown"}:
            reason = "preserve or review original audio"
        elif at < previous_end + .12:
            reason = "effect collision"
        elif context not in {"quiet", "music", "narration"}:
            reason = "unrecognized audio context"
        elif context == "music" and music_bed is None:
            reason = "music bed required for level proposal"
        ranked = []
        if reason is None:
            for item in entries:
                if item.get("kind") != "sfx":
                    continue
                origin = item.get("origin", {})
                if origin.get("audit", {}).get("status") != "passed":
                    continue
                if item.get("rights") not in {"owned", "licensed", "permission"}:
                    continue
                reviewed = (item.get("reuse_status") == "reusable" and
                            item.get("effect_review") == "passed" and
                            item.get("sfx_profile", {}).get("identification_review") == "passed")
                if mode == "delivery" and not reviewed:
                    continue
                roles = origin.get("cue_roles", [])
                match = next((i for i, role in enumerate(ROLES[kind]) if role in roles), None)
                if match is None:
                    continue
                sync = origin.get("sync", {})
                anchor = "peak_s" if kind in {"move", "cut", "reveal"} else "onset_s"
                start = at - float(sync.get(anchor, 0))
                duration = float(item["media"]["duration_seconds"])
                if start < 0 or start + duration > manifest["duration_seconds"] + .01:
                    continue
                family = origin.get("sound_id", "").split("/")[0]
                style_bonus = (len(STYLE_FAMILIES[style]) - STYLE_FAMILIES[style].index(family)
                               if family in STYLE_FAMILIES[style] else 0)
                ranked.append((10 - match * 2 + style_bonus, duration, item["id"], item, start,
                               reviewed, anchor))
        ranked.sort(key=lambda row: (-row[0], row[1], row[2]))
        if not ranked and reason is None:
            reason = "no suitable eligible sound"
        if reason:
            output.append({"event_id": event["id"], "decision": "no-effect", "reason": reason,
                           "evidence": event.get("evidence")})
            continue
        _, duration, _, item, start, reviewed, anchor = ranked[0]
        gain = .18 if context == "narration" else .4
        level_evidence = {"method": "context_default"}
        if context == "music":
            gain, level_evidence = _music_gain(music_bed, at, assets / item["relative_path"])
            level_evidence["method"] = "pre_cue_50ms_window_measurement"
        output.append({"event_id": event["id"], "decision": "candidate",
                       "asset_id": item["id"], "sound_id": item["origin"]["sound_id"],
                       "asset_sha256": item["sha256"], "asset_path": item["relative_path"],
                       "start": round(start, 5), "event_time": at,
                       "duration": duration, "sync_anchor": anchor,
                       "gain": gain, "audio_context": context,
                       "level_evidence": level_evidence,
                       "review_status": "pending_review",
                       "sound_review_required": not reviewed,
                       "evidence": event.get("evidence")})
        previous_end = start + duration
    return {"schema_version": 1, "route": manifest["route"], "mode": mode,
            "source": manifest["source"], "source_sha256": manifest["source_sha256"],
            "duration_seconds": manifest["duration_seconds"], "style": style,
            "music_bed_sha256": _sha(music_bed) if music_bed else None,
            "cues": output, "timeline_changed": False}


def export_timeline(proposal: dict, timeline_path: Path, assets: Path, output: Path) -> dict:
    """Write a revision input only; the timeline tool owns immutable revisions."""
    root = HERE.parents[2] / "timeline" / "scripts"
    sys.path.insert(0, str(root))
    import model  # noqa: E402

    timeline = model.load(timeline_path)
    model.validate(timeline, require_review=False)
    if proposal["route"] != "edited" or proposal["source_sha256"] != timeline["picture"][0]["sha256"]:
        raise ValueError("Proposal is not bound to this edited picture")
    if len(timeline["picture"]) != 1 or timeline["picture"][0]["source_in"] != 0:
        raise ValueError("SFX export expects one supplied edited picture")
    draft = Path(timeline["source_root"])
    cues = list(timeline["audio"])
    for index, cue in enumerate(proposal["cues"]):
        if cue["decision"] != "candidate":
            continue
        source = assets / cue["asset_path"]
        if _sha(source) != cue["asset_sha256"]:
            raise ValueError("SFX catalogue file changed")
        target = draft / ".content-studio" / "audio" / "sfx" / (cue["asset_sha256"] + ".wav")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        cues.append({"id": f"sfx-{index:04d}", "kind": "sfx",
                     "source": target.relative_to(draft).as_posix(),
                     "sha256": cue["asset_sha256"], "start": cue["start"],
                     "gain": cue["gain"], "review_status": "pending_review",
                     "asset_id": cue["asset_id"], "event_id": cue["event_id"],
                     "sound_review_required": cue["sound_review_required"]})
    if output.exists():
        raise ValueError("Changes file already exists")
    output.write_text(json.dumps({"audio": cues}, indent=2) + "\n", encoding="utf-8")
    return {"changes": str(output), "sfx_cues": len(cues) - len(timeline["audio"])}


def export_remotion(proposal: dict, project: Path, assets: Path, output: Path,
                    public_dir: Path) -> dict:
    if proposal["route"] != "remotion":
        raise ValueError("Remotion proposal required")
    project = project.resolve()
    output = output.resolve()
    public_dir = public_dir.resolve()
    entry = project / "entry.tsx"
    if output != project / "content" / "sfx-cues.json" or not entry.is_file():
        raise ValueError("Remotion export needs <video>/entry.tsx and <video>/content/sfx-cues.json")
    authored = entry.read_text(encoding="utf-8")
    if authored.count("component={Video}") != 1 or "Content Studio SFX overlay" in authored:
        raise ValueError("Remotion entry needs one canonical Video composition to mount SFX")
    plan_path = project / "scene-plan.json"
    if not plan_path.is_file() or _sha(plan_path) != proposal["source_sha256"]:
        raise ValueError("Remotion scene plan changed after SFX proposal")
    fps = json.loads(plan_path.read_text(encoding="utf-8"))["fps"]
    clips = []
    for index, cue in enumerate(proposal["cues"]):
        if cue["decision"] != "candidate":
            continue
        source = assets / cue["asset_path"]
        if _sha(source) != cue["asset_sha256"]:
            raise ValueError("SFX catalogue file changed")
        target = public_dir / "sfx" / (cue["asset_sha256"] + ".wav")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        clips.append({"id": f"sfx-{index:04d}", "kind": "sfx",
                      "src": "/sfx/" + target.name, "start": cue["start"],
                      "duration": cue["duration"], "volume": cue["gain"],
                      "sha256": cue["asset_sha256"],
                      "asset_id": cue["asset_id"],
                      "sound_review_required": cue["sound_review_required"]})
    if output.exists():
        raise ValueError("Remotion cues file already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": 1, "source_sha256": proposal["source_sha256"],
                                  "clips": clips, "review_status": "pending_review"}, indent=2) + "\n",
                      encoding="utf-8")
    # The standard composition entry mounts the declaration once. The delivery
    # validator can then require this marker and exact cue/audio hashes.
    overlay = ("import sfxCues from './content/sfx-cues.json';\n"
               "import {MediaLayer} from '@raghu-vijaykumar/videogen/runtime/components/media/MediaLayer';\n"
               f"// Content Studio SFX overlay: generated from the reviewed cue manifest.\n"
               f"const SfxVideo = () => <><Video/><MediaLayer clips={{sfxCues.clips as any}} fps={{{fps}}}/></>;\n")
    entry.write_text(overlay + authored.replace("component={Video}", "component={SfxVideo}"),
                     encoding="utf-8")
    return {"cues": str(output), "sfx_clips": len(clips), "mounted_in": str(entry)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    edited = actions.add_parser("analyze-edited")
    edited.add_argument("--video", type=Path, required=True)
    edited.add_argument("--evidence-dir", type=Path, required=True)
    edited.add_argument("--output", type=Path, required=True)
    edited.add_argument("--scene-threshold", type=float, default=.35)
    remotion = actions.add_parser("analyze-remotion")
    remotion.add_argument("--plan", type=Path, required=True)
    remotion.add_argument("--output", type=Path, required=True)
    proposal = actions.add_parser("propose")
    proposal.add_argument("--events", type=Path, required=True)
    proposal.add_argument("--library", type=Path, default=sfx.library.STOCK_ASSETS)
    proposal.add_argument("--style", choices=sorted(STYLE_FAMILIES), default="calm")
    proposal.add_argument("--mode", choices=["preview", "delivery"], default="preview")
    proposal.add_argument("--music-bed", type=Path)
    proposal.add_argument("--output", type=Path, required=True)
    for action in ("export-timeline", "export-remotion"):
        entry = actions.add_parser(action)
        entry.add_argument("--proposal", type=Path, required=True)
        entry.add_argument("--library", type=Path, default=sfx.library.STOCK_ASSETS)
        entry.add_argument("--output", type=Path, required=True)
        entry.add_argument("--timeline" if action == "export-timeline" else "--project", type=Path, required=True)
        if action == "export-remotion":
            entry.add_argument("--public-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "analyze-edited":
            data = analyze_edited(args.video, args.evidence_dir, args.scene_threshold)
        elif args.action == "analyze-remotion":
            data = analyze_remotion(args.plan)
        elif args.action == "propose":
            data = propose(json.loads(args.events.read_text(encoding="utf-8")),
                           args.library, args.style, args.mode, args.music_bed)
        elif args.action == "export-timeline":
            data = export_timeline(json.loads(args.proposal.read_text(encoding="utf-8")),
                                   args.timeline, args.library, args.output)
        else:
            data = export_remotion(json.loads(args.proposal.read_text(encoding="utf-8")),
                                   args.project, args.library, args.output, args.public_dir)
        if args.action.startswith("analyze") or args.action == "propose":
            if args.output.exists():
                raise ValueError("Output already exists")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"output": str(args.output), "count": len(data.get("events", data.get("cues", [])))}))
        else:
            print(json.dumps(data))
    except (ValueError, OSError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"SFX {args.action} failed: {exc}\n")


if __name__ == "__main__":
    main()
