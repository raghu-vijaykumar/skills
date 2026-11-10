# Reusable stock catalogue

This repository catalogues **designs and methods**. Full-resolution generated
assets and your private media catalogue live outside Git; the small GIFs below
are review examples derived from the approved CTA exports. Select a design,
review its motion on the target footage, then render the approved size and
position. All CTA designs are original drawings; no reference-video pixels or
audio are used.

## Like / Share / Subscribe CTA

| Variant ID | Animated example | Look | Output and availability |
| --- | --- | --- | --- |
| `classic-bar` | ![Classic bar CTA over fountain footage](previews/classic-bar.gif) | Cream connected bar with teal/coral accents | Like → Share → Subscribe → Subscribed → bell → exit; silent transparent ProRes 4444 generator supported. |
| `minimal-pills` | ![Minimal pills CTA over fountain footage](previews/minimal-pills.gif) | Three separated dark translucent pills; active chips light up | Same timed sequence; silent transparent ProRes 4444 generator supported. |
| `bold-stack` | ![Bold stack CTA over fountain footage](previews/bold-stack.gif) | Vertical three-card stack with a large subscribe row | Same timed sequence; silent transparent ProRes 4444 generator supported. |

The GIFs use a still from the [published Dubai Fountain video](https://www.youtube.com/watch?v=yWKZaxVK-6I)
at 95 seconds as a placement background. The animation comes from the exact
reviewed alpha clips in the private stock library; the GIFs are silent and
downscaled. See the [reproduction notes](previews/cta-variants.md).

All three accept `top-right`, `top-left`, `bottom-right`, `bottom-left`, or `center`. The common review target is 3840×2160, 30 fps, five seconds. `classic-bar` is the default so existing approved commands remain valid. See [motion graphics](../edit/motion-graphics/README.md) for per-video placement and HLG composition. Placement is chosen per shot; these are selectable assets, not automatic end cards.

## Private authored assets

Run from the source repository root. The library destination must be a private local folder outside this repository:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> init
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> add --file <my-sticker.png> --name "My sticker" --kind sticker --rights owned --creator "Raghu" --tags "cooking,smile"
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> list --kind sticker
```

The local library writes `catalogue.json`, `README.md`, and `media/<type>/...`. `README.md` lists only actual imported assets with name, type, dimensions, rights, creator, tags, and a relative media link. Supported types are `cta`, `meme`, `gif`, `sticker`, and `stock-clip`; files are decoded/probed and deduplicated by SHA-256. External sources are copied; files already inside the library are indexed in place. Rights must be confirmed as `owned`, `licensed`, or `permission`. Keep private media, generated previews, and its local catalogue out of source control.

The separate [memes catalogue](../memes/README.md) handles user-supplied reaction material and scene-based insertion proposals. A self-created meme can be kept here as reusable stock; insertion into a video still goes through the meme skill's contextual review or an approved timeline.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `cta-variants` | Supported | Named design, size, rate, duration, placement → silent transparent ProRes clip | No | [Animated variants](#like--share--subscribe-cta) and [exact-asset review notes](previews/cta-variants.md) | Full asset production follows the approved Content Studio precheck; the generic delivery timeline cannot yet compose this alpha clip. |
| `authored-assets` | Supported | Authorized self-created media and metadata → private SHA-256 catalogue and README | No | [Importer tests](tests/test_stock_library.py) | Private local folder outside Git; contextual meme insertion remains in the memes skill. |
