# Feature Specification: Complete headless Blender capability roadmap

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: In progress

## User scenarios and testing

### P1: Plan a 3D scene without naming a style

A Content Studio author describes a subject and teaching beat. The editable production plan proposes a subject, visual style, mood or world when relevant, animation approach, and executable route. Explicit choices take precedence. A route without a demonstrated builder is identified before rendering.

**Acceptance**: Each of the 94 pinned upstream IDs has one catalog record with dependencies, route, status, and evidence. A request with no style yields a reviewable proposal; an explicit style is preserved; unsupported combinations return `needs_builder` rather than a rendered claim.

### P2: Compare outputs and show the best rendered result

An author can review every full-render candidate for a route. Each candidate has technical results, five editorial scores, hashes, reviewer, and reason. The best candidate that passes the gates appears in the root README as a GIF; rejected candidates remain in the score record.

**Acceptance**: No `Rendered` or `Integrated` status is published without a scored selected GIF matching its recorded hash. A higher-scoring valid candidate replaces a lower-scoring one. Failed or unscored candidates cannot be selected. Every visual style has a distinct reviewed GIF; a shared GIF for other routes must visibly demonstrate each claimed capability.

### P3: Render an editable, resumable shot

An author can preview, render, interrupt, and resume a trusted project-owned Blender shot. The shot preserves stable object and beat IDs, source rights, frame cues, render settings, and required review states. The resulting MP4, editable scene, and report are verifiable.

**Acceptance**: Resume covers every required frame exactly once, rejects changed inputs, checks working space before batches, and produces the same reviewed frame sequence as an uninterrupted render. The exact MP4 passes dimensions, frame count, duration, hash, and representative visual review.

### P4: Use the remaining craft, technical, style, setting, and export routes

An author can choose each named route in the catalog and see a runnable example and applicable visual or structural evidence. Original benchmark assets can serve multiple craft routes. Distinct styles must differ through scene construction, materials, motion, framing, light, or compositing as appropriate.

**Acceptance**: Waves 2–6 each have executable examples and scored output artifacts. Modeling and production routes additionally verify applicable geometry, topology, UV, material, rig, or cache properties. Export routes verify scale, hierarchy, materials, animation, and collision after Blender reimport. Actual Unity, Unreal, and Godot editor imports remain labeled pending unless tested in those editors.

### P5: Hand an approved shot to a video

A code-driven Content Studio project registers an approved Blender shot by project-relative path, SHA-256, origin, and license note. It is placed at the intended narration cue and reviewed as a hero, in the composition, and in the exact final render.

**Acceptance**: The existing videogen asset validator accepts the registered shot and rejects a changed or unlisted file. Real drafts follow the workflow precheck and current-plan approval before production editing. Edited-video timeline support is claimed only after its own adapter and tests exist.

## Functional requirements

- Preserve the single `content-studio-video-animation` skill and immutable upstream MIT attribution; add no vendor skill copy.
- Keep the 94-row README generated from the maintained catalog. Statuses are `Catalogued`, `Prototype`, `Rendered`, and `Integrated`, with evidence gates for each advance.
- Keep the existing `make_scene(spec, spec_dir)` builder interface for bounded previews and full renders.
- Score every full-render candidate and retain the score even when it is rejected. Publish only the highest-scoring technically valid GIF per route.
- Use original procedural assets for generic showcases. Imported assets require documented rights and source hashes.
- Run diagnosis and creative review on exact encoded outputs; a GIF is a visible summary, not proof of structural quality or production approval.
- Commit logically complete routes and requested optimized GIFs on `main`; keep large MP4s, `.blend` files, caches, and private assets outside Git.

## Success criteria

- Exactly 94 distinct catalog entries resolve to the pinned upstream commit, with no unsupported status claims.
- Every named route has its planned or implemented Content Studio method, dependency list, and honest evidence state; every completed route has its applicable runnable and visual or structural proof.
- Every full-render candidate used for showcase selection has a complete score record; every committed showcase GIF is the top-scoring candidate that passed technical checks.
- All 31 core, extended, and horror visual treatments have distinct reviewed GIFs. Worlds, moods, genres, and era routes show recognizable authored results rather than keyword labels.
- The renderer passes interruption/resume, changed-input, missing-frame, disk-space, media-probe, and exact-output tests.
- Relevant Python, Blender, documentation, capability, and videogen tests pass for each completed release slice.

## Assumptions

- The three existing showcases are the starting evidence and receive retrospective editorial scores. Their single-candidate winners remain provisional until a competing render exists.
- Multiple non-style routes may share a GIF when the evidence note shows the relevant behavior or structure for each. Structural routes also require non-visual checks.
- A successful export and Blender reimport does not claim validation inside a game engine editor.
