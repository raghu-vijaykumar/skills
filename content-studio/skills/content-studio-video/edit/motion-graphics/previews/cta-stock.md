# Transparent CTA example

Illustrative command; no 4K ProRes asset is committed. The renderer needs Pillow,
FFmpeg, and FFprobe.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/cta_stock.py render --output <content-assets>/like-share-subscribe-uhd-alpha.mov --width 3840 --height 2160 --fps 30 --duration 5.0 --position top-right
```

Output is silent, transparent UHD ProRes 4444. Check alpha and every button state in a
composite preview. Other formats or frame rates need a fresh render.
