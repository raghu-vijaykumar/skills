---
name: content-studio-vlog
description: Prepare vlog camera clips, review a manual edit export, transcribe it locally, and propose a title, description, captions, and thumbnail for approval.
---

# Content Studio Vlog

For a configured channel draft, run `python <bundle>/toolkit/content-helper/scripts/content.py order --channel <slug> --draft <id> --dry-run` to inspect the mixed-device capture order. `order` writes `_timeline.csv` and numbers camera files by capture time. Existing timeline timestamps, including estimated ones, remain fixed when new clips arrive; only new clips are probed and all camera numbers are reassigned. Supply `--utc-offset +04:00` when the cameras' local offset cannot be inferred. The full preprocessing command below refreshes stale ordering automatically.

Run `python <bundle>/toolkit/content-helper/scripts/content.py preprocess --channel <slug> --draft <id>` on camera clips. Its report flags blur and excessive stabilization crop; only approved blur spans are cut. Originals remain untouched by preprocessing. Dolby Vision exports must retain RPU and frame alignment or fall back to the untouched video plus cleaned audio. Read the toolkit's preprocessing instructions for its exact review flags.

Use `content.py edit trim --input <clip> --start 00:12 --end 00:30 --out <clip-trim.mp4>` to keep a range, or `content.py edit cut --input <clip> --remove 00:12-00:14 --out <clip-cut.mp4>` to remove one or more ranges. These are frame-accurate renders. SDR and HLG cuts keep their respective color tags; Dolby Vision cuts require explicit `--sdr`, because a frame-accurate re-encode cannot retain its RPU. Each output path must be new. `content.py edit join --channel <slug> --draft <id>` joins all ordered clips, preferring approved cuts and processed audio/video where available, into `draft/video.mp4`. The joined master is 1920x1080 BT.709 SDR at 30 fps; HDR clips are tone mapped and 4:3 clips are padded to keep the full frame. For a curated sequence, repeat `--input <clip>` in desired order and pass `--out <video.mp4>`. Review the resulting edit before publication.

When the final `video.mp4` is present, run `node <bundle>/scripts/cli.mjs transcribe --channel <slug> --draft <id>`; run `powershell -File <bundle>/scripts/setup-whisper.ps1` once if needed; transcription uses pinned local `whisper.cpp`, writes a transcript and caption draft, and checks audio/video metadata. Read the transcript alongside representative frames, correct names and place references, then draft several truthful titles and a description.

Use image generation with the transcript and representative frames as references to make a thumbnail candidate. Show the generated image to the user and get approval before writing `thumbnail.png`. Present the final title, description, captions, and video for human review. Only after approval may `content-studio-publish` record package approval and publish at the requested time.
