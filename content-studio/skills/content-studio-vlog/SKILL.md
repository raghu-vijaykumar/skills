---
name: content-studio-vlog
description: Prepare vlog camera clips, review a manual edit export, transcribe it locally, and propose a title, description, captions, and thumbnail for approval.
---

# Content Studio Vlog

For a configured channel draft, run `python <bundle>/toolkit/content-helper/scripts/content.py preprocess --channel <slug> --draft <id>` on camera clips. Its report flags blur and excessive stabilization crop; only approved blur spans are cut. Originals remain untouched. Dolby Vision exports must retain RPU and frame alignment or fall back to the untouched video plus cleaned audio. Read the toolkit's preprocessing instructions for its exact review flags.

The human assembles and exports the vlog. When the final `video.mp4` is present, run `node <bundle>/scripts/cli.mjs transcribe --channel <slug> --draft <id>`; run `powershell -File <bundle>/scripts/setup-whisper.ps1` once if needed; transcription uses pinned local `whisper.cpp`, writes a transcript and caption draft, and checks audio/video metadata. Read the transcript alongside representative frames, correct names and place references, then draft several truthful titles and a description.

Use image generation with the transcript and representative frames as references to make a thumbnail candidate. Show the generated image to the user and get approval before writing `thumbnail.png`. Present the final title, description, captions, and video for human review. Only after approval may `content-studio-publish` record package approval and publish at the requested time.
