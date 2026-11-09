# HLG composition example

Illustrative command; the narrow HLG route needs exact hashes and human approval.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py --manifest <approved-manifest.json>
```

Supports only 3840x2160/30, 48 kHz input audio, a five-second intro and CTA, and the
named operations. It cannot preserve a Dolby Vision RPU. The generic delivery timeline
remains SDR-only.
