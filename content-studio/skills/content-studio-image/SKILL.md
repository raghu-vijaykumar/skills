---
name: content-studio-image
description: Create reviewed Content Studio images using reusable UI themes or original character illustration styles, with visual samples for every choice.
---

# Content Studio image

Open the [visual catalog](README.md) when choosing a look. UI themes and character illustration styles are separate:

- A [UI theme](catalog/styles.json) changes surfaces, typography, color and accents on structured information. The same request-flow diagram is rendered in every theme README, including Bento box, minimalism, glassmorphism and neumorphism. Content decides whether the design needs a diagram, chart, list, comparison or another layout.
- A [character style](catalog/character-styles.json) guides image generation for an original person or mascot. Anime, watercolor, comic ink, 3D animation, pixel art and collage have individual READMEs with images of the same character. Use the image generation tool with a reviewed brief; [character_prompt.py](scripts/character_prompt.py) can produce a stable style-specific prompt.

For production, run the mandatory [Content Studio precheck](../content-studio-workflow/SKILL.md) and obtain approval for the specific plan and render or generation prompt. Review the reference brief, identity, sources and asset rights. Preview the chosen look, then inspect the final image at delivery size. A generated illustration is not evidence for a factual claim.

For structured content, use [render.py](scripts/render.py) directly. It accepts one reviewed JSON card and a UI theme ID, and writes editable SVG, PNG, hashes and a review page. It does not depend on a presets plan. See the [content contract](references/content.md). The example in the gallery can be rendered with:

```powershell
python content-studio/skills/content-studio-image/scripts/render.py render --input content-studio/skills/content-studio-image/examples/request-flow.json --style bento-box --output tmp/image-bento
```

For a character image, preserve the subject description across candidate styles, generate bounded previews using the image generation tool, then choose and review one. Start a prompt with:

```powershell
python content-studio/skills/content-studio-image/scripts/character_prompt.py --style anime --brief content-studio/skills/content-studio-image/examples/character-brief.txt
```

Treat the character gallery as examples of looks, not guaranteed deterministic outputs. Keep final generated assets and their review records in the user's draft workspace. Use [requirements.txt](requirements.txt) if CairoSVG and Pillow are unavailable. `sample-theme` extracts provisional colors from a reference; confirm them before rendering.
