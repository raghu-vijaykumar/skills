# Instagram Reel SFX method guide

`reel_sfx.py` uses yt-dlp, FFmpeg, and FFprobe. It accepts a public Instagram Reel URL, strips tracking parameters, downloads the source without cookies or access bypasses, and records a small `.source.json` with its hash and creator. `extract` exports exact bounded PCM WAV candidates with a JSON sidecar. A cut is always pending effects-only review and has unknown rights by default.

Before extracting, check a standalone licensed source where the effect can be identified or replaced with a reviewed similar sound. Record the item page, creator/provider, license terms, and target-platform permissions; never claim a similar sound is the Reel's exact original. The user or editor identifies any remaining effect ranges by listening to the source and checking the video. Exported candidates are only candidates: speech and music can overlap an audible effect. If the effect cannot be isolated cleanly, retain it as a reference or recreate a new owned effect in a separate reviewed workflow.

The private [stock catalogue](../../stock-library/README.md) owns accepted SFX and their WAVs; they are not bundled into this skill. Run `python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> list --kind sfx` to browse them. Verify each source range, file hash, rights, and effects-only review before using it. Reel assets with unknown rights remain `reference-only`.

For overlapping dialogue or music, a separately approved source-separation comparison can produce experimental stems. Preserve the raw cut, record the model and checkpoint hash, parameters, upload destination if any, source and stem hashes, and the editor's decision. Listen to the whole candidate: a separator may remove part of a desired laugh or leave speech in an effects stem. The extractor itself only cuts audio and never asserts that a derived stem is clean.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `reel-download` | Supported | Public Reel URL → private MP4 and source record | No | [Focused tests](tests/test_reel_sfx.py) | Public access only; platform availability can change. |
| `sfx-extract` | Supported | Approved source and seconds → PCM WAV candidate and sidecar | No | [Focused tests](tests/test_reel_sfx.py) | Does not separate overlapping voice or music; requires listening review. |
