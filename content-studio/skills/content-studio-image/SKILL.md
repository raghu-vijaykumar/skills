---
name: content-studio-image
description: Create reviewed Content Studio images using reusable UI themes or original character illustration styles, with visual examples for character styles.
---

# Content Studio image

Open the [visual catalog](README.md) when choosing a look. UI themes and character illustration styles are separate:

- A [UI theme](catalog/styles.json) changes surfaces, typography, color and accents on structured information. Bento box, minimalism, glassmorphism and neumorphism are defined independently from content layout. Content decides whether the design needs a diagram, chart, list, comparison or another layout. The theme READMEs describe each treatment without sample diagrams.
- A [character style](catalog/character-styles.json) guides image generation for an original person or mascot. Anime, watercolor, comic ink, 3D animation, pixel art and collage have individual READMEs with images of the same character. Use the image generation tool with a reviewed brief; [character_prompt.py](scripts/character_prompt.py) can produce a stable style-specific prompt.

For production, run the mandatory [Content Studio precheck](../content-studio-workflow/SKILL.md) and obtain approval for the specific plan and render or generation prompt. Review the reference brief, identity, sources and asset rights. Preview the chosen look, then inspect the final image at delivery size. A generated illustration is not evidence for a factual claim.

For structured content, use [render.py](scripts/render.py) directly. It accepts one reviewed JSON card and a UI theme ID, and writes editable SVG, PNG, hashes and a review page. It does not depend on a presets plan. See the [content contract](references/content.md). Render a reviewed card from your draft with:

```powershell
python content-studio/skills/content-studio-image/scripts/render.py render --input draft/card.json --style bento-box --output draft/image-review
```

For a character image, preserve the subject description across candidate styles, generate bounded previews using the image generation tool, then choose and review one. Start a prompt with:

```powershell
python content-studio/skills/content-studio-image/scripts/character_prompt.py --style anime --brief content-studio/skills/content-studio-image/examples/character-brief.txt
```

Treat the character gallery as examples of looks, not guaranteed deterministic outputs. Keep final generated assets and their review records in the user's draft workspace. Use [requirements.txt](requirements.txt) if CairoSVG and Pillow are unavailable. `sample-theme` extracts provisional colors from a reference; confirm them before rendering.
