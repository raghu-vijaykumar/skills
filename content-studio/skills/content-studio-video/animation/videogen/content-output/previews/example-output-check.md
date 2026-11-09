# Carousel/post output example

Illustrative command/output example. No rendered card is committed here because the
output depends on an installed Remotion project and its registered formats.

```powershell
node content-studio/skills/content-studio-video/animation/videogen/content-output/scripts/content-check.mjs <project> <edition>
node content-studio/skills/content-studio-video/animation/videogen/content-output/scripts/content-render.mjs <project> <edition>
```

`content-check` validates the package against the registered carousel/post format and
returns a non-zero exit on an unsupported format. `content-render` writes the card or
animated edition and its manifest. Inspect every card or GIF at final size.
