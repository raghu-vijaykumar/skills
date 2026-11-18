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

- [x] T010 [P4] Author the eight core styles with distinct scored GIFs and explicit recipe differences.
  - [x] T010a Render the low-poly lamp treatment with a distinct scored GIF and a 184-triangle flat-shading audit.
  - [x] T010b Render the voxel lamp treatment with a distinct scored GIF and a 0.05 m occupancy-grid audit.
  - [x] T010c Render the isometric one-tile lamp treatment with a distinct scored GIF and a locked true-iso camera audit.
  - [x] T010d Render the measured realistic clamp lamp treatment with a distinct scored GIF and a PBR-scale audit; retain its documented photoreal limits.
  - [x] T010e Render the narrow psychological horror corridor with a distinct scored GIF and a fog/light/spatial audit.
  - [x] T010f Render the PSX horror CRT hall with a distinct scored GIF and a low-resolution texture/geometry audit.
  - [x] T010g Render the anime heroine with a distinct scored GIF and a cel-band, outline, and pose-control audit.
  - [x] T010h Render the storybook windmill island with a distinct scored GIF and a shape/palette/paint audit.
- [x] T011 [P4] Author the fifteen extended styles with distinct scored GIFs and explicit recipe differences.
  - [x] T011a Render the cartoon ball mascot with a scored GIF and a squash/stretch audit.
  - [x] T011b Render the comic rocket panel with a scored GIF and a print, ink, and impact audit.
  - [x] T011c Render the manga eye panel with a scored GIF and a grayscale, screentone, and gaze audit.
  - [x] T011d Render the pixel treasure chest with three scored outputs and a texel, palette, and motion audit.
  - [x] T011e Render the hand-painted wildflower teacup with two scored candidates and a painted UV, matte material, and steam audit.
  - [x] T011f Render the scene-wide watercolor river with three scored candidates and a pigment, paper, sail, and motion audit.
  - [x] T011g Render the paper-craft butterfly with two scored candidates and a fiber, layer, seam, and held-pose audit.
  - [x] T011h Render the chibi courier with two scored candidates and a head-ratio, postal-prop, blink, and hop audit.
  - [x] T011i Render the noir detective with two scored candidates and a silhouette, lighting, wet-street, and walk audit.
  - [x] T011j Render the minimalist pendulum with two scored candidates and a palette, negative-space, and swing audit.
  - [x] T011k Render the vector sprout with three scored candidates and a flat-fill, growth, and polygon-path audit.
  - [x] T011l Render the retro 8-bit ship with two scored candidates and a four-color, sprite-grid, and held-motion audit.
  - [x] T011m Render the retro 16-bit fox with two scored candidates and a packed-dither, palette, fox-walk, and waterfall audit.
  - [x] T011n Render the HD-2D lantern bridge with three scored candidates and a pixel-actor, painted-stage, lighting, and DOF audit.
  - [x] T011o Render the Frutiger Aero dashboard with two scored candidates and a glossy-aqua, leaf, bubble-trail, and UI audit.
- [ ] T012 [P4] Author the eight horror packs with distinct scored GIFs and explicit recipe differences.
  - [x] T012a Render the cosmic aperture with three scored candidates and a tiny-witness, broken-geometry, moving-iris, and void audit.
  - [x] T012b Render the body-horror hand with three full renders, four scored GIF outputs, and a corrected sixth-digit anatomy audit.
  - [x] T012c Render the analog training tape with three scored candidates and a scanline, signal-loss, security-camera, and doorway audit.
  - [x] T012d Render the empty poolrooms with two scored candidates and a modular-bay, fluorescent, water, and inspection-push audit.
  - [ ] T012e Complete the remaining four horror packs with distinct scored GIFs.

## Wave 5: Settings and genre direction

- [ ] T013 [P4] Author ten worlds and moods, thirteen genre directions, and the console-era route with scored recognizable results.

## Wave 6: Delivery and QA

- [ ] T014 [P4] Implement optimization, LOD, collision, generic export, and Unity/Unreal/Godot export adapters with Blender reimport assertions.
- [ ] T015 [P4] Complete QA review across the 94 rows, reconcile statuses and selected GIFs, and label actual engine-editor imports pending until verified.
- [ ] T016 [P1-P5] Run all applicable repository and exact-render gates, inspect the full 94-route completion audit, commit and push complete slices on `main`.

## Dependency order

T001–T006 enable the route builders. The first audited craft benchmark in T007a supports an early T010a style treatment, reflecting the priority on distinct animation styles. Remaining T007–T009 and T010–T013 proceed in independently verified slices; a style example does not advance its standalone material or lighting dependencies. T014–T016 complete export and final audit. Each logical route may be committed and pushed before later waves finish.
