# Transparent CTA and HLG intro composition

Select a design from the [stock library](../../../stock-library/README.md) and generate the CTA after the approved Content Studio precheck. The generator draws 4K RGBA frames and encodes ProRes 4444 with alpha; it does not use the pixels or audio of a reference clip. Verify `pix_fmt` contains `a` with `ffprobe`, and inspect frames during Like, Share, Subscribe, Subscribed, and bell states over real video. Use another `--position` to make a distinct full-frame transparent placement. Do not add this to every video without reviewing the closing shot.

`ingredient_list.heading` changes only the list heading. Existing cue sheets retain the old default. To replace a baked overlay, start from the clean edited source, remove the old CTA event, and regenerate the ASS sidecar. Pixel removal from the baked preview is not a reliable substitute.

The HLG composer manifest uses explicit file hashes and a fixed supported operation set:

```json
{
  "schema_version": 1,
  "revision": 1,
  "plan": {"path": "<approved preflight plan.json>", "sha256": "<sha256>"},
  "source": {"path": "<clean UHD30 HLG source.mp4>", "sha256": "<sha256>"},
  "intro": {"path": "<UHD30 SDR intro.mp4>", "sha256": "<sha256>"},
  "cues": {"path": "<revised cues.json>", "sha256": "<sha256>"},
  "sidecar": {"path": "<revised overlay.ass>", "sha256": "<sha256>"},
  "stock": {"path": "<UHD30 alpha CTA.mov>", "sha256": "<sha256>"},
  "intro_seconds": 5.0,
  "stock_start": 482.0,
  "stock_duration": 5.0,
  "video": {"width": 3840, "height": 2160, "fps": 30,
            "codec": "hevc-main10", "color": "bt2020-hlg"},
  "audio_policy": "concat-original"
}
```

Run these commands after reviewing all paths and hashes:

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py validate --manifest <manifest.json>
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py preview --manifest <manifest.json> --out-dir <review-folder>
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/hdr_compose.py fingerprint --manifest <manifest.json>
```

Review the intro seam, ingredient segment, and closing CTA previews. Record only a genuine human approval of the exact fingerprint in JSON with `actor: "human"`, `fingerprint`, and `review_note`. Then run `render --manifest <manifest.json> --approval <approval.json> --output <new-master.mp4>` and `verify --manifest <manifest.json> --video <new-master.mp4> --evidence-dir <review-folder>`. `render` refuses an existing final output. A changed manifest, input, or composer script invalidates approval.

The intro is converted from full-range SDR through linear RGB to BT.2020/HLG so its original colors remain close after a round trip. The clean main picture stays in 10-bit HLG without tone mapping. The source's Dolby Vision RPU is not retained after compositing. Review color on an HLG-capable display, compare unaffected frames with the clean source, listen across the five-second audio boundary, and watch the exact master before package approval. The verifier checks technical properties and saves frames; its report leaves subjective human review pending.
