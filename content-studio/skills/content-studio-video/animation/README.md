# Animation

Code-driven video uses [videogen](videogen/SKILL.md); original Blender shots use the shared [headless route](references/blender-art.md). The [rendered gallery scenes](blender/README.md) are authored examples. The [upstream Blender Skills snapshot](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d) informs the catalog and craft instructions, but does not supply executable Blender methods.

`Supported` here means a callable method exists for its specified input; it does not make every catalogued skill an automatic renderer. `Specialist only` means the result is reviewed as a separate asset before composition.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `blender-catalog` | Supported | Maintained 94-ID capability manifest → classified catalog | No | [Catalog tests](blender/tests/test_catalog.py) | Rendered status requires local proof; most entries are still guidance. |
| `blender-plan` | Supported | Visual request and optional style → suggested subject, style, and narrowly matching gallery builder | No | [Routing tests](blender/tests/test_catalog.py) | Requires creative review; unsupported combinations have no builder. |
| `blender-shot` | Supported | Trusted `make_scene` builder and JSON spec → editable `.blend`, MP4, hash report; optional resumable frame cache | Specialist only | [Three opening examples](blender/review.md) · [Desk lamp craft audit](blender/lamp-review.md) · [Low-poly treatment](blender/lowpoly-review.md) · [Voxel treatment](blender/voxel-review.md) · [Isometric treatment](blender/isometric-review.md) · [Realistic product treatment](blender/realistic-review.md) · [Psychological horror treatment](blender/horror-review.md) · [PSX horror treatment](blender/psx-horror-review.md) · [Anime heroine treatment](blender/anime-review.md) · [Version 2 contract](blender/shot-contract.md) · [Resume comparison](blender/resume-review.md) | Blender 5.3 tested; project owns geometry and animation. |
| `blender-handoff` | Supported | Reviewed Blender report and MP4, narration WAV, cue → hashed videogen project and Remotion source | No | [Scored composed render](blender/handoff-review.md) · [Handoff tests](blender/tests/test_handoff.py) | Code-driven video path only; production drafts need approved precheck. |
