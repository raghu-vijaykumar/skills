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

## Shared installation

The existing global skills installation is pinned to bundle version 0.6.1 and
cannot discover a newly added leaf in that immutable release. Bump the private
package to 0.6.2, keep the lockfile version aligned, run the full package and
capability-matrix gates, then use the managed installer with the global skills
parent as an explicit target. Verify the new leaf junction resolves to the
versioned installation. Preserve the older release for rollback.

Verification: bundle 0.6.2 installed 66 managed skill links. The stock-library
link resolved into the 0.6.2 bundle, its skill files matched source hashes,
the installed CTA command listed all three variants, and the 0.6.1 bundle
remained available.
