# Implementation plan: post themes and character styles

## Constitution check

Keep the canonical implementation inside `content-studio-image`. Use portable JSON cards and no production credentials. Inspect rendered post examples at delivery size. The user explicitly requested catalog example media, so the small gallery assets belong in Git; production draft media does not.

## Design

1. Add ten different, clearly illustrative post cards under `examples/post-themes/` and render each with its matching UI theme.
2. Extend the renderer's text/list surfaces where needed so Bento, glass, neumorphic and other treatments are visible on post copy, not only on diagrams.
3. Add a gallery builder that regenerates the UI SVG/PNG samples and per-theme READMEs from the maintained catalog and example cards.
4. Expand `catalog/character-styles.json` to 30 styles grouped by medium. Generate one original-character sample per new style with the built-in image generator. Keep the same identity and framing in prompts.
5. Build root and per-style READMEs, update the image skill and tests, and verify all links and actual gallery images.

## Validation

Run focused image tests, regenerate and inspect the UI gallery, verify every listed style has a readable sample and README, run docs checks, stage only this feature, review the staged diff, commit and push on main.
