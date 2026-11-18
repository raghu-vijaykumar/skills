"""Package one reviewed Blender MP4 as a hashed videogen cue example."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-show_entries",
         "stream=codec_type,width,height,nb_read_frames:format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def package(report_path, video, narration, out, title, cue_id, cue_start, video_license,
            narration_license, narration_origin="generated"):
    """Copy only verified media, then author a scene plan and playable composition."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (video.suffix.lower() != ".mp4" or narration.suffix.lower() != ".wav"
            or not video.is_file() or not narration.is_file()):
        raise ValueError("Handoff requires an MP4 shot and WAV narration")
    if not all((title.strip(), cue_id.strip(), video_license.strip(), narration_license.strip())):
        raise ValueError("Title, cue ID, and both rights notes are required")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", cue_id):
        raise ValueError("Narration cue ID must use lowercase letters, numbers, and hyphens")
    if narration_origin not in {"generated", "recorded", "licensed"}:
        raise ValueError("Narration origin must describe its actual source")
    if cue_start < 0:
        raise ValueError("Cue start must be nonnegative")
    if digest(video) != report.get("video", {}).get("sha256"):
        raise ValueError("Blender MP4 differs from its render report")
    meta = probe(video)
    streams = [s for s in meta["streams"] if s["codec_type"] == "video"]
    if (len(streams) != 1 or int(streams[0]["nb_read_frames"]) != report["frames"]
            or [streams[0]["width"], streams[0]["height"]] != report["resolution"]):
        raise ValueError("Blender MP4 fails its exact frame and resolution report")
    if report["fps"] <= 0:
        raise ValueError("Invalid Blender source frame rate")
    clip_frames = round(report["frames"] * 30 / report["fps"])
    if clip_frames < 1:
        raise ValueError("Blender shot is too short for the 30 fps composition")
    audio = probe(narration)
    if not any(s["codec_type"] == "audio" for s in audio["streams"]):
        raise ValueError("Narration WAV has no audio stream")
    if float(audio["format"]["duration"]) > clip_frames / 30:
        raise ValueError("Narration runs past the reviewed Blender shot")
    duration = cue_start + clip_frames
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("Use a new empty handoff folder")
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(video, assets / "shot.mp4")
    shutil.copy2(narration, assets / "narration.wav")
    manifest = {"schemaVersion": 1, "assets": [
        {"id": "shot", "path": "assets/shot.mp4", "sha256": digest(assets / "shot.mp4"),
         "origin": "procedural", "license": video_license},
        {"id": "narration", "path": "assets/narration.wav",
         "sha256": digest(assets / "narration.wav"), "origin": narration_origin,
         "license": narration_license},
    ]}
    scene = {"id": "blender-hero", "type": "hero", "startFrame": 0, "endFrame": duration,
             "title": title, "visual": {"videoId": "shot", "videoStartFrame": cue_start},
             "stateChanges": [{"frame": 0, "label": "Await cue"},
                              {"frame": cue_start, "label": "Show reviewed 3D motion"}]
             if cue_start else [{"frame": 0, "label": "Show reviewed 3D motion"}],
             "camera": [{"frame": 0, "scale": 1}], "assetIds": ["shot", "narration"],
             "narrationCueIds": [cue_id], "sourceIds": [], "audioCueIds": ["narration"]}
    plan = {"schemaVersion": 1, "width": report["resolution"][0],
            "height": report["resolution"][1], "fps": 30, "durationFrames": duration,
            "title": title, "scenes": [scene]}
    (out / "asset-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "scene-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    # Sequence uses the same frame as visual.videoStartFrame; its audio starts with the shot.
    (out / "video.tsx").write_text(
        "import React from 'react';\n"
        "import {AbsoluteFill, Audio, OffthreadVideo, Sequence} from 'remotion';\n"
        "import shot from './assets/shot.mp4';\n"
        "import narration from './assets/narration.wav';\n"
        f"export const Video = () => <AbsoluteFill style={{{{background: '#0b111a'}}}}><Sequence from={{{cue_start}}}>"
        "<OffthreadVideo src={shot} muted style={{width: '100%', height: '100%', objectFit: 'contain'}}/>"
        "<Audio src={narration}/></Sequence></AbsoluteFill>;\n",
        encoding="utf-8",
    )
    (out / "entry.tsx").write_text(
        "import React from 'react';\nimport {Composition, registerRoot} from 'remotion';\n"
        "import {Video} from './video';\n"
        f"const Root = () => <Composition id=\"BlenderHandoff\" component={{Video}} width={{{plan['width']}}} "
        f"height={{{plan['height']}}} fps={{30}} durationInFrames={{{duration}}}/>;\nregisterRoot(Root);\n",
        encoding="utf-8",
    )
    (out / "handoff.json").write_text(json.dumps({"source_report_sha256": digest(report_path),
        "source_video_sha256": digest(video), "narration_sha256": digest(narration),
        "cue_id": cue_id, "cue_start_frame": cue_start, "composition_frames": duration}, indent=2) + "\n",
        encoding="utf-8")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "video", "narration", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("title", "cue-id", "video-license", "narration-license"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--cue-start-frame", type=int, default=0)
    parser.add_argument("--narration-origin", choices=("generated", "recorded", "licensed"),
                        default="generated")
    args = parser.parse_args()
    plan = package(args.report, args.video, args.narration, args.out, args.title,
                   args.cue_id, args.cue_start_frame, args.video_license,
                   args.narration_license, args.narration_origin)
    print(f"Packaged {plan['durationFrames']} frames at cue {args.cue_id}: {args.out}")


if __name__ == "__main__":
    main()
