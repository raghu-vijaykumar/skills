# Implementation plan: image themes and character styles

## Constitution check

One canonical implementation under `content-studio-image`; portable input paths and canvas dimensions; actual rendered samples reviewed; tests cover public script behavior; no generated draft media or credentials in Git. Catalog samples are committed because the user expressly requested visual READMEs.

## Design

- Store UI themes in `catalog/styles.json` with palette, font and treatment. Keep data layout selection in `render.py`, based on content fields.
- Render one fixed `examples/request-flow.json` through every UI theme. Generate per-theme PNG/SVG/README and one comparison sheet.
- Store character illustration styles in `catalog/character-styles.json`. Use one fixed original character brief for six image-generation samples. Keep each sample and README in its own style folder.
- Use `scripts/character_prompt.py` to create reproducible style prompts for arbitrary original characters. The image generation tool creates production character artwork; the helper does not claim deterministic image output.
- Make `render.py render --input --style --output` independent of the unfinished presets catalog. Emit editable SVG, PNG, hashes and review HTML.
- Keep production approval and source/rights review in the existing workflow skill.

## Validation

Run focused Python tests, regenerate the visual gallery, inspect its comparison image and character samples, validate the skill, run repository documentation checks, then stage only this slice and review the staged diff.
