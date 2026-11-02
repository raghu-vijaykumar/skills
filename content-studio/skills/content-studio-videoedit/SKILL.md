---
name: content-studio-videoedit
description: Assemble a vlog from preprocessed clips, then review its edited export, transcript, captions, and thumbnail. Use after clip preprocessing or when a final manual export is supplied.
---

# Content Studio Video Edit

This skill also owns the shared channel helper used by archive, ideagen, and preprocessing for backup, Drive sync, analytics, capture ordering, and preprocessing. Read [the channel helper](references/channel-helper.md) for those commands and their workspace conventions.

Read the channel rules and draft timeline. For a simple edit, use `python <this-skill>/scripts/content.py edit trim --input <clip> --start 00:12 --end 00:30 --out <new-clip>` or `edit cut --input <clip> --remove 00:12-00:14 --out <new-clip>`. `edit join --channel <slug> --draft <id>` assembles ordered clips, preferring approved cuts and processed outputs. For a curated sequence, repeat `--input <clip>` in the desired order and set `--out`. Review every transition and the full result. Manual editing remains available for complex assembly.

Edits are frame accurate. SDR and HLG cuts keep their respective color tags; Dolby Vision cuts require explicit `--sdr` because their RPU cannot survive a frame accurate re-encode. Each output path must be new. The automatic joined master is 1920x1080 BT.709 SDR at 30 fps, with HDR tone mapping and 4:3 padding. Read the [edit guide](references/channel-helper.md) before using those commands.

When the final `video.mp4` is present, run `node <bundle>/scripts/cli.mjs transcribe --channel <slug> --draft <id>`. If needed, install the pinned local multilingual `whisper.cpp` with `powershell -File <bundle>/scripts/setup-whisper.ps1`. Review `transcript.json` and `captions.srt` against the audio and representative frames; correct names, places, and timing. Draft truthful titles and a description from the actual export.

Generate a thumbnail candidate from the transcript and representative frames. Show the image to the user and obtain approval before writing `thumbnail.png`. Present the master, title, description, captions, and thumbnail together for review. Hand the approved package to `content-studio-publish`; publication still needs the user's explicit request.
