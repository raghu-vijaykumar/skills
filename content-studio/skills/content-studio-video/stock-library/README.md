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

## Private authored assets and sound-effect references

Run from the source repository root. The library destination must be a private local folder outside this repository:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> init
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> add --file <my-sticker.png> --name "My sticker" --kind sticker --rights owned --creator "Raghu" --tags "cooking,smile"
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> list --kind sticker
```

The local library writes `catalogue.json`, `README.md`, and `media/<type>/...`. `README.md` lists only actual imported assets with name, type, dimensions or duration, rights, creator, review status, source, tags, and a relative media link. Supported types are `cta`, `meme`, `gif`, `sticker`, `stock-clip`, and `sfx`; files are decoded/probed and deduplicated by SHA-256. External sources are copied; files already inside the library are indexed in place. Visual assets require confirmed `owned`, `licensed`, or `permission` rights. Keep private media, generated previews, and its local catalogue out of source control.

For a sound effect sourced from a public Reel, use [reel SFX](../audio/reel-sfx/SKILL.md) to download and export a candidate after the approved production precheck. Listen to the complete candidate and record whether it contains only the intended effect. An unlicensed source is `unknown` even if the effect sounds generic. This example records a private reference entry and does **not** authorize reuse:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> add --file <candidate.wav> --name "Short effect name" --kind sfx --rights unknown --creator "Source creator" --tags "sfx,comedy" --source-url "https://www.instagram.com/reel/<id>/" --source-start <seconds> --source-end <seconds> --source-sha256 <source-hash> --effect-review pending
```

The `reference-only` status blocks reuse when rights are unknown or the effects-only listening review is pending or failed. After rights and isolation are confirmed, use `library.py --library <private-library> review --id <stock-id> --rights permission --effect-review passed --note "<listening and permission evidence>"` to update the existing entry. This records a human decision, not an automatic speech-removal result. Do not index a cut containing audible voice as an effect.

The separate [memes catalogue](../memes/README.md) handles user-supplied reaction material and scene-based insertion proposals. A self-created meme can be kept here as reusable stock; insertion into a video still goes through the meme skill's contextual review or an approved timeline.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `cta-variants` | Supported | Named design, size, rate, duration, placement → silent transparent ProRes clip | No | [Animated variants](#like--share--subscribe-cta) and [exact-asset review notes](previews/cta-variants.md) | Full asset production follows the approved Content Studio precheck; the generic delivery timeline cannot yet compose this alpha clip. |
| `authored-assets` | Supported | Reviewed visual assets or SFX reference and provenance → private SHA-256 catalogue and README | No | [Importer tests](tests/test_stock_library.py) | Unknown-rights or unreviewed SFX are reference-only; contextual meme insertion remains in the memes skill. |
