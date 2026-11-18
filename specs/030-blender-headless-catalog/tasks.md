# Tasks: Blender headless capability catalog

**Input**: [spec.md](spec.md) and [plan.md](plan.md)

## Foundation

- [x] T001 Pin upstream source and MIT attribution in `content-studio/skills/content-studio-video/animation/references/blender-art.md`.
- [x] T002 Implement catalog classification, validation, and README table generation under `content-studio/skills/content-studio-video/animation/blender/`.
- [x] T003 Extend the existing animation skill and method matrix under `content-studio/skills/content-studio-video/animation/`.
- [x] T004 Implement a shared full-shot runner using the existing `make_scene` contract under `content-studio/skills/content-studio-video/animation/blender/scripts/`.

## US1: Find a route

- [x] T005 [US1] Test 94 unique catalog entries, resolved source paths, auto routing, explicit overrides, and unsupported status in `content-studio/skills/content-studio-video/animation/blender/tests/`.
- [x] T006 [US1] Generate the full root `README.md` capability table and document truthful status definitions.

## US2: Three rendered showcases

- [x] T007 [US2] Author the mechanical clamp builder and specification in `content-studio/skills/content-studio-video/animation/blender/examples/`.
- [x] T008 [US2] Author the cel-shaded character builder and specification in `content-studio/skills/content-studio-video/animation/blender/examples/`.
- [x] T009 [US2] Author the atmospheric corridor builder and specification in `content-studio/skills/content-studio-video/animation/blender/examples/`.
- [x] T010 [US2] Render and review bounded frames and full clips; generate and verify three GIFs under `content-studio/skills/content-studio-video/animation/blender/previews/`.
- [x] T011 [US2] Embed the three GIFs with evidence and rebuild commands in the root `README.md` and Blender skill README.

## US3: Content Studio handoff

- [x] T012 [US3] Document hashed asset handoff to code-driven videogen and production precheck in the existing animation skill and `blender/README.md`.

## Release

- [x] T013 Run focused tests, documentation and capability checks; inspect exact renders and staged diff; commit and push only this feature on `main`.
