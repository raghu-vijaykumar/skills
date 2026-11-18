# Feature Specification: Blender headless capability catalog

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: Implemented

## User scenarios

### P1: Find a suitable Blender route without naming a style

An author describes a 3D subject or teaching beat. Content Studio selects relevant Blender craft and a visual treatment, presents the choice in the normal reviewable plan, and distinguishes guidance from executable support.

**Acceptance**: All 94 pinned upstream skills are indexed once. An omitted style selects a relevant route; an explicit style remains authoritative. Unsupported combinations do not claim render support.

### P2: See three actual animated capabilities

An author can inspect a realistic mechanical prop, a cel-shaded character, and an atmospheric environment in the root README. Each GIF comes from a reproducible Blender render with source, frame review, and evidence.

**Acceptance**: Three different headless scene builders produce editable scenes, bounded frames, a full motion output, and optimized GIFs that visibly show the claimed action.

### P3: Carry a reviewed Blender shot into Content Studio

A code-driven video project can register the generated shot as a hashed asset and review it in the narrated composition. A production draft follows the existing precheck and approval route.

**Acceptance**: The handoff contract records source, render settings, and asset hash. The documented route does not claim support in the edited-video delivery timeline.

## Requirements

- Pin upstream skill references by immutable commit and adapt useful craft guidance in the existing video animation skill. Retain source and MIT attribution without copying the upstream skill tree.
- Publish a complete 94-row README table driven by one catalog source of truth, with truthful support and evidence fields.
- Preserve the existing `make_scene(spec, spec_dir)` preview contract and use the same builder for full renders.
- Verify asset provenance, object IDs, frame range, resolution, rendered frames, and exact GIF source.
- Keep source builders, specifications, rebuild commands, and review evidence linked to every showcase.
- Use approved imported assets only when provenance and rights are recorded. The first three may use original procedural assets.
- Follow the Content Studio human-reviewed production precheck for real drafts. Publication remains separate.

## Success criteria

- The catalog contains exactly 94 unique names and every source URL points to the pinned commit.
- Each of the three showcase GIFs depicts a distinct, inspectable motion and links to its Blender source and rebuild route.
- Blender 5.3 renders all three examples and selected frames match the encoded output.
- `npm run check:docs` and focused catalog and Blender tests pass.

## Assumptions

- This feature implements the foundation and first three composite showcases. The remaining named craft and style routes stay catalogued for later reviewed features.
- Unity, Unreal, and Godot exports remain planned after the first showcases; Blender round-trip verification is the first export gate.
