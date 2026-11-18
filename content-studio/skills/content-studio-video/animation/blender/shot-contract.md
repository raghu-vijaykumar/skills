# Headless Blender shot contract

New authored shots use [version 2 JSON](examples/clamp-contract-v2.json) with the existing `make_scene(spec, spec_dir)` builder. The first three gallery specifications remain readable as version 1 evidence; new capability routes should use version 2. The contract is validated before a full render, then compared with the scene the builder actually creates.

| Field | Meaning |
| --- | --- |
| `schema_version`, `id` | Version `2` and a stable lowercase shot ID. |
| `width`, `height`, `fps`, `frames` | Reviewed delivery geometry and frame range; the full renderer refuses a different size. |
| `render_engine`, `color_transform`, `codec` | Exact Blender render engine, color transform, and H.264 output profile. |
| `camera_object`, `objects` | Camera name and unique stable object IDs paired with Blender object names. All declared names must exist in the built scene. |
| `beats`, `review_states` | Ordered initial, action, and result beats with frame numbers, labels, and referenced object IDs. The named review states select frames to inspect. |
| `assets` | Every source asset has an ID, origin, and rights note. Procedural assets are represented by builder dependencies; imported files require a relative path and matching SHA-256. |

Run the bounded [frame preview](../engineering-3d/references/headless-preview.md) at the contract's review frames, then render the same builder with `blender/scripts/render_shot.py`. The full-shot report includes the validated IDs, beat frames, imported asset hashes, Blender version, source hashes, MP4 hash, dimensions, and encoded frame count. A passing contract or encode is still followed by motion review and [candidate scoring](README.md#score-and-select-output-artifacts). The [version 2 smoke scene](examples/clamp-contract-v2.json) passed a three-frame 320×240 Blender 5.3 render; it is a contract test, not another gallery candidate.
