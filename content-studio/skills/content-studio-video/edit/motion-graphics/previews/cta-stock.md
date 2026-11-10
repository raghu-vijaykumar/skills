# Transparent CTA example

The compatibility command delegates to the stock library generator. Its
[classic-bar animation](../../../stock-library/previews/classic-bar.gif) is a
review GIF composited from the actual approved transparent UHD asset. No full
ProRes asset is committed. Select `classic-bar`, `minimal-pills`, or `bold-stack`
in the [stock library](../../../stock-library/README.md). The renderer needs Pillow,
FFmpeg, and FFprobe.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/cta_stock.py render --output <content-assets>/like-share-subscribe-uhd-alpha.mov --width 3840 --height 2160 --fps 30 --duration 5.0 --position top-right
```

Output is silent, transparent UHD ProRes 4444. Check alpha and every button state in a
composite preview. Other formats or frame rates need a fresh render.
