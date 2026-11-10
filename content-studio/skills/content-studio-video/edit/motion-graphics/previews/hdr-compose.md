# HLG composition example

Illustrative command; the narrow HLG route needs exact hashes and human approval.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py validate --manifest <manifest.json>
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py preview --manifest <manifest.json> --out-dir <review-folder>
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py fingerprint --manifest <manifest.json>
# After genuine human approval of that exact fingerprint:
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py render --manifest <manifest.json> --approval <approval.json> --output <new-master.mp4>
```

Supports only 3840x2160/30, 48 kHz input audio, a five-second intro and CTA, and the
named operations. It cannot preserve a Dolby Vision RPU. The generic delivery timeline
remains SDR-only.
