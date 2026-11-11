# Plan: Instagram Reel sound effects

- Place the new leaf under `content-studio-video/audio/reel-sfx`. Use `yt-dlp` for download and FFmpeg/FFprobe for source validation and PCM segment export. Keep output under a caller-supplied private folder.
- Write sidecar JSON beside each candidate with source URL, creator, source hash, boundaries, output hash, and pending voice review. Do not run source separation automatically; overlapped speech needs explicit review or a separate approved isolation method.
- Add `sfx` to the existing stock-library importer and retain catalogue schema version 1 for existing private libraries. Add optional provenance and review fields; show reference-only status in its generated README.
- Document the user-facing workflow and method limitations. Add focused tests for the new CLI and catalogue behavior, then run skill discovery, docs, capability, and Python tests.
- Profile the supplied reel and prepare a byte-bound precheck plan with exact commands and review criteria. Only after the user approves that revision, extract candidates and import those that pass the voice check. Keep unknown-rights entries private and reference-only.
- For recognizable effects, research standalone official-library files before proposing reuse. Compare them as candidates, carry their license evidence into any new production plan, and ask the editor to choose if an exact match cannot be verified.
- For mixed Reel audio, allow a separately approved experimental stem comparison. Record model/checkpoint and service provenance, preserve raw cuts, and catalogue only the editor-selected complete effects-only version.
