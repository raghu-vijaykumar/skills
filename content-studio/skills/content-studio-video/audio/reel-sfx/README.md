# Instagram Reel SFX method guide

`reel_sfx.py` uses yt-dlp, FFmpeg, and FFprobe. It accepts a public Instagram Reel URL, strips tracking parameters, downloads the source without cookies or access bypasses, and records a small `.source.json` with its hash and creator. `extract` exports exact bounded PCM WAV candidates with a JSON sidecar. A cut is always pending effects-only review and has unknown rights by default.

The user or editor identifies effect ranges by listening to the source and checking the video. Exported candidates are only candidates: speech and music can overlap an audible effect. If the effect cannot be isolated cleanly, retain it as a reference or recreate a new owned effect in a separate reviewed workflow.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `reel-download` | Supported | Public Reel URL → private MP4 and source record | No | [Focused tests](tests/test_reel_sfx.py) | Public access only; platform availability can change. |
| `sfx-extract` | Supported | Approved source and seconds → PCM WAV candidate and sidecar | No | [Focused tests](tests/test_reel_sfx.py) | Does not separate overlapping voice or music; requires listening review. |
