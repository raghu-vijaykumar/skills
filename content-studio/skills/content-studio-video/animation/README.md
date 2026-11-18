# Animation

Code-driven video uses [videogen](videogen/SKILL.md); original Blender shots use the shared [headless route](references/blender-art.md). The [three gallery scenes](blender/README.md) are authored examples. The [upstream Blender Skills snapshot](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d) informs the catalog and craft instructions, but does not supply executable Blender methods.

`Supported` here means a callable method exists for its specified input; it does not make every catalogued skill an automatic renderer. `Specialist only` means the result is reviewed as a separate asset before composition.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `blender-catalog` | Supported | Maintained 94-ID category map → classified catalog | No | [Catalog tests](blender/tests/test_catalog.py) | Category guidance only. |
| `blender-plan` | Supported | Visual request and optional style → suggested subject and style | No | [Routing tests](blender/tests/test_catalog.py) | Requires creative review; no automatic scene builder choice. |
| `blender-shot` | Supported | Trusted `make_scene` builder and JSON spec → editable `.blend`, MP4, hash report | Specialist only | [Three rendered examples](blender/review.md) | Blender 5.3 tested; project owns geometry and animation. |
