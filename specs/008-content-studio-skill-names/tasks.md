# Tasks

- [x] Define seven canonical skill names and the preprocessing/edit boundary.
- [x] Update skill folders, entrypoints, router, docs, installer, and project sync.
- [x] Validate package, skill discovery, clean install, and content checks.
- [x] Commit and push the immutable release, pin content, and verify remote heads.

## Verification

- Skills tag `videogen-v0.4.1` resolves to `855f5953c498aef7d91293abb0c861b276c7a118`; the published content pin resolves to that commit.
- Skills: 21 Node tests, 25 content-helper Python tests, 4 idea-planner tests, 2 digest tests, seven skill validators, docs gate, package contents check, and clean tagged checkout passed.
- A real local whisper.cpp v1.9.4 run on a six-second speech fixture produced a timed transcript, captions, and three frames; transcript wording still requires human correction.
- Content: 301 local tests passed. A fresh remote clone installed the tag and passed 300 tests with one media-cache-dependent skip; documentation passed.
- Global installation exposes seven version-matched links; superseded idea, animation, and vlog names were removed. The retired snapshot's unrelated local changes were preserved.
