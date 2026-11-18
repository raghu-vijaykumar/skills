# Tasks: Complete headless Blender capability roadmap

**Input**: [spec.md](spec.md) and [plan.md](plan.md). Check a task only after its stated evidence is inspected.

## Wave 0: Shared foundation

- [x] T001 [P1] Replace category-only data with the 94-entry capability manifest and status validation in `animation/blender/`.
- [x] T002 [P1] Connect the scene-aware style planner to reviewed Blender examples and explicit subject/style overrides in `planning/styles/`.
- [x] T003 [P2] Score all three existing full-render candidates, record their hashes and visual reasons, and gate rendered README rows on the best valid GIF in `animation/blender/`.
- [x] T004 [P3] Define and validate the full shot specification: stable object and beat IDs, provenance, cues, render settings, and required review states in `animation/blender/`.
- [x] T005 [P3] Implement input-hashed resumable frame batches, durable logs, completion marker, free-space precheck, and exact MP4 assembly in `animation/blender/scripts/`.
- [x] T006 [P5] Register a Blender MP4 in a synthetic videogen project's asset manifest, place it at a narration cue, and verify the exact composed output.

## Wave 2: Asset craft

- [ ] T007 [P4] Build original benchmark assets and reusable modeling, topology, UV, material, texture, groom, cloth, and lookdev routes with structural checks and scored moving proof.
  - [x] T007a Render and structurally audit the measured desk lamp for `blender-modeler` and `prop-artist`; score and publish its best GIF.
  - [ ] T007b Complete the remaining modeling, topology, UV, material, texture, groom, cloth, and lookdev examples.
- [ ] T008 [P4] Complete procedural modeling, scene assembly, set dressing, and archviz examples and record route-specific evidence.

## Wave 3: Technical motion and rendering

- [ ] T009 [P4] Implement Geometry Nodes, camera, lighting, rendering, compositing, animation, rigging, VFX, and physics examples with baked-cache or structural checks where applicable.

## Wave 4: Visual treatments

- [ ] T010 [P4] Author the eight core styles with distinct scored GIFs and explicit recipe differences.
  - [x] T010a Render the low-poly lamp treatment with a distinct scored GIF and a 184-triangle flat-shading audit.
  - [x] T010b Render the voxel lamp treatment with a distinct scored GIF and a 0.05 m occupancy-grid audit.
  - [x] T010c Render the isometric one-tile lamp treatment with a distinct scored GIF and a locked true-iso camera audit.
  - [x] T010d Render the measured realistic clamp lamp treatment with a distinct scored GIF and a PBR-scale audit; retain its documented photoreal limits.
  - [ ] T010e Complete the remaining four core style treatments with distinct scored GIFs.
- [ ] T011 [P4] Author the fifteen extended styles with distinct scored GIFs and explicit recipe differences.
- [ ] T012 [P4] Author the eight horror packs with distinct scored GIFs and explicit recipe differences.

## Wave 5: Settings and genre direction

- [ ] T013 [P4] Author ten worlds and moods, thirteen genre directions, and the console-era route with scored recognizable results.

## Wave 6: Delivery and QA

- [ ] T014 [P4] Implement optimization, LOD, collision, generic export, and Unity/Unreal/Godot export adapters with Blender reimport assertions.
- [ ] T015 [P4] Complete QA review across the 94 rows, reconcile statuses and selected GIFs, and label actual engine-editor imports pending until verified.
- [ ] T016 [P1-P5] Run all applicable repository and exact-render gates, inspect the full 94-route completion audit, commit and push complete slices on `main`.

## Dependency order

T001–T006 enable the route builders. The first audited craft benchmark in T007a supports an early T010a style treatment, reflecting the priority on distinct animation styles. Remaining T007–T009 and T010–T013 proceed in independently verified slices; a style example does not advance its standalone material or lighting dependencies. T014–T016 complete export and final audit. Each logical route may be committed and pushed before later waves finish.
