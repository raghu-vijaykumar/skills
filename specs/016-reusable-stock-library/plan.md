# Plan: Reusable Content Studio stock library

## Design

- Place the canonical CTA drawing/rendering code under `content-studio-video/stock-library/scripts/`. Keep the old motion-graphics entrypoint as a thin compatibility wrapper.
- Add `classic-bar`, `minimal-pills`, and `bold-stack` visual choices. A `list` command exposes them; `render --variant` selects one. Preserve `classic-bar` pixel logic for existing callers.
- Use a separate private authored-asset library with an atomic JSON index and generated `README.md`. This records owned reusable media, while the existing memes skill continues to own reaction search and insertion proposals. No private media or absolute machine path enters Git.
- Add a stock skill README for built-in designs, and point the parent, motion-graphics, and memes skills to it. The stock skill routes video insertion to existing approved timelines and compositors; it does not claim generic timeline support.

## Verification

- Run focused Python tests and `npm run check:docs`.
- Draw representative frames of each style over a synthetic background and inspect the result as bounded design evidence. Production media render and any import of the approved existing CTA follow a separate Content Studio precheck and human approval.
- Stage only feature files, review the staged diff, commit, push, and verify remote HEAD.
