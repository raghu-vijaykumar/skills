# Tasks

- [x] Specify the catalog and project-enabled style boundaries.
- [x] Add the skill, list script, routing, installer, and version update.
- [x] Test style outputs, eight-skill discovery, package build, and content checks.
- [x] Release and pin the tag, update owner documents, and verify remote heads.

## Verification

- The immutable `videogen-v0.4.2` tag resolves to `de6514bc5acace2c744f3a86787e72071bcd2d46`; the content lockfile resolves to the same commit.
- The built-in catalog lists four styles and two separate themes. Revise Labs enables four styles; a clean neutral project enables only Core Explainer.
- Skills: 21 Node tests, 25 content-helper Python tests, 4 idea-planner tests, 2 digest tests, eight skill validators, docs gate, package contents check, and clean tagged checkout passed.
- All eight global links point to v0.4.2; no superseded global names remain. Content passed 301 local tests and 300 tests with one expected media-cache skip in a fresh remote clone. Content and retired-snapshot docs gates passed.
- The active content commit is `38e175ffcffcffde8a7947c4d0faae7045c3849b`; the retired snapshot pointer commit is `006f6a1eb4200966df46fe9ed2d3fa01dc661c1d`. Existing video folders were not changed, and unrelated local edits were preserved.
