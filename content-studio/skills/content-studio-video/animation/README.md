# Animation

Code-driven video uses [videogen](videogen/SKILL.md); original Blender shots use the shared [headless route](references/blender-art.md). The [rendered gallery scenes](blender/README.md) are authored examples. The [upstream Blender Skills snapshot](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d) informs the catalog and craft instructions, but does not supply executable Blender methods.

`Supported` here means a callable method exists for its specified input; it does not make every catalogued skill an automatic renderer. `Specialist only` means the result is reviewed as a separate asset before composition.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `blender-catalog` | Supported | Maintained 94-ID capability manifest → classified catalog | No | [Catalog tests](blender/tests/test_catalog.py) | Rendered status requires local proof; most entries are still guidance. |
| `blender-plan` | Supported | Visual request and optional style → suggested subject, style, and narrowly matching gallery builder | No | [Routing tests](blender/tests/test_catalog.py) | Requires creative review; unsupported combinations have no builder. |
| `blender-shot` | Supported | Trusted `make_scene` builder and JSON spec → editable `.blend`, MP4, hash report; optional resumable frame cache | Specialist only | [Three opening examples](blender/review.md) · [Desk lamp craft audit](blender/lamp-review.md) · [Low-poly treatment](blender/lowpoly-review.md) · [Voxel treatment](blender/voxel-review.md) · [Isometric treatment](blender/isometric-review.md) · [Realistic product treatment](blender/realistic-review.md) · [Psychological horror treatment](blender/horror-review.md) · [PSX horror treatment](blender/psx-horror-review.md) · [Anime heroine treatment](blender/anime-review.md) · [Stylized windmill treatment](blender/stylized-review.md) · [Cartoon mascot treatment](blender/cartoon-review.md) · [Comic rocket treatment](blender/comic-review.md) · [Manga close-up treatment](blender/manga-review.md) · [Pixel art chest treatment](blender/pixel-review.md) · [Painted teacup treatment](blender/painted-review.md) · [Watercolor river treatment](blender/watercolor-review.md) · [Paper craft butterfly treatment](blender/paper-review.md) · [Version 2 contract](blender/shot-contract.md) · [Resume comparison](blender/resume-review.md) | Blender 5.3 tested; project owns geometry and animation. |
| `blender-handoff` | Supported | Reviewed Blender report and MP4, narration WAV, cue → hashed videogen project and Remotion source | No | [Scored composed render](blender/handoff-review.md) · [Handoff tests](blender/tests/test_handoff.py) | Code-driven video path only; production drafts need approved precheck. |

The [`chibi-style` courier](blender/chibi-review.md) is another scored `blender-shot` treatment with a distinct full-body proportion and motion audit.
The [`noir-style` detective](blender/noir-review.md) adds scored hard-light, silhouette, and wet-street evidence.
The [`minimalist-style` pendulum](blender/minimal-review.md) adds a scored three-color, negative-space, and swing audit.
The [`vector-style` sprout](blender/vector-review.md) adds a scored flat-fill, staged-growth, and polygon-path audit.
The [`retro-8bit-style` ship](blender/retro8-review.md) adds a scored four-color sprite, held-motion, and impact audit.
The [`retro-16bit-style` fox](blender/retro16-review.md) adds a scored packed-dither landscape, held walk, and waterfall audit.
The [`hd-2d-style` lantern bridge](blender/hd2d-review.md) adds a scored pixel actor, painted 3D stage, and depth-of-field audit.
The [`frutiger-aero-style` dashboard](blender/aero-review.md) adds a scored glossy aqua UI, floating bubble, and leaf-opening audit.
The [`cosmic-eldritch-horror` aperture](blender/cosmic-review.md) adds a scored vast-void scene, tiny witness, and shifting-geometry audit.
The [`body-horror-style` hand](blender/hand-review.md) adds a scored six-digit mutation, skin-to-metal fusion, and articulated-finger audit.
The [`analog-found-footage-horror` tape](blender/analog-review.md) adds a scored security-room recording, tracking-line, monitor-signal, and implied-figure audit.
The [`liminal-space-style` poolrooms](blender/liminal-review.md) add a scored empty modular hall, fluorescent flicker, and long inspection-push audit.
