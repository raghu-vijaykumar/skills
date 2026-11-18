# Structured image content

The image renderer accepts one JSON card directly. It uses the card's content to choose a diagram, chart, comparison or list arrangement; the selected UI theme changes its visual treatment. The [common gallery card](../examples/request-flow.json) is rendered unchanged in all ten themes.

- `title` is required. Optional `subtitle`, `sourceNote` and `altText` provide context and accessibility.
- `nodes`: `{id,label,x?,y?,symbol?}`. Optional positions are normalized `0..1`. Symbols can be `terminal`, `service`, `queue`, `process`, `database` or `cloud`. `edges`: `{from,to,label}` with a meaningful relationship label.
- `data`: `{label,value}` with finite nonnegative values. Also provide `unit` and `sourceNote`.
- `comparison`: exactly two `{label,points}` sides.
- `steps` or `points`: short text or `{heading,text}` entries. `body` supports one statement.
- `claims`: when included, factual claims need `sourceUrl`. `assets`: when included, each needs rights set to `owned`, `licensed`, `permission` or `original`.

Use the same renderer at different canvas sizes; width, height and safe margin are output decisions. A generated illustration is separate from evidence. The renderer rejects unknown diagram relationships, unsupported node symbols and crowded text rather than silently guessing.

```powershell
python content-studio/skills/content-studio-image/scripts/render.py render --input content-studio/skills/content-studio-image/examples/request-flow.json --style glassmorphism --width 1080 --height 1350 --margin 81 --output tmp/image-glass
```

The editable SVG and PNG have hashes in `manifest.json`. Inspect the PNG and `review.html` before use. Character generation instead uses [character_prompt.py](../scripts/character_prompt.py) and the image generation tool; see the [character catalog](../catalog/character-styles.json).
