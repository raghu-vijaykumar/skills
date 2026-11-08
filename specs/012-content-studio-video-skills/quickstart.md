# Quickstart validation

1. Run `npm run check:docs`; all nested and compatibility skill links must resolve.
2. Install into an empty temporary target with `node content-studio/scripts/cli.mjs install-skills --target <temp>`. Verify every nested name is directly discoverable and old names still resolve.
3. Run `npm test` and the repository's focused Python skill suites. Run `node content-studio/scripts/cli.mjs --help`, the migrated enhancement/benchmark help routes, and a package-import smoke test.
4. Inspect a raw-folder precheck and handoff plan: no AutoCut, join, voice, upscale, or overlay step should execute by default.
5. Inspect a supplied-render plan: voice script and approved voice precede any full-edit upscale, which precedes code-generated overlays.
6. Verify the four prompts, both READMEs, AGENTS.md, and the structure document distinguish implemented paths from future methods.
