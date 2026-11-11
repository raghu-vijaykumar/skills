# Reusable stock catalogue

This repository catalogues **designs, methods, and owned CTA assets**. The
[asset catalogue](assets/README.md) and full-resolution CTA clips live in this
skill's `assets/` folder. The small GIFs below are review examples derived
from the approved CTA exports. Select a design,
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
reviewed alpha clips in this skill's assets folder; the GIFs are silent and
downscaled. See the [reproduction notes](previews/cta-variants.md).

All three accept `top-right`, `top-left`, `bottom-right`, `bottom-left`, or `center`. The common review target is 3840×2160, 30 fps, five seconds. `classic-bar` is the default so existing approved commands remain valid. See [motion graphics](../edit/motion-graphics/README.md) for per-video placement and HLG composition. Placement is chosen per shot; these are selectable assets, not automatic end cards.

## Git catalogue and local sound-effect references

Run from the source repository root. This skill's `assets/` folder owns the catalogue. The source repository tracks the catalogue and owned CTA clips; `assets/media/sfx/` is ignored by Git while the sourced Reel WAVs have unknown redistribution rights:

```powershell
$stock = 'content-studio/skills/content-studio-video/stock-library/assets'
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock init
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock add --file <my-sticker.png> --name "My sticker" --kind sticker --rights owned --creator "Raghu" --tags "cooking,smile"
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock list --kind sticker
```

The asset folder contains `catalogue.json`, `README.md`, and `media/<type>/...`. `README.md` lists actual imported assets with name, type, dimensions or duration, rights, creator, review status, source, tags, and a relative media link. Supported types are `cta`, `meme`, `gif`, `sticker`, `stock-clip`, and `sfx`; files are decoded/probed and deduplicated by SHA-256. External sources are copied; files already inside the library are indexed in place. Visual assets require confirmed `owned`, `licensed`, or `permission` rights. Keep generated review evidence out of Git. Commit only media whose redistribution rights are confirmed.

For a sound effect sourced from a public Reel, use [reel SFX](../audio/reel-sfx/SKILL.md) to download and export a candidate after the approved production precheck. Listen to the complete candidate and record whether it contains only the intended effect. An unlicensed source is `unknown` even if the effect sounds generic. This example records a private reference entry and does **not** authorize reuse:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock add --file <candidate.wav> --name "Short effect name" --kind sfx --rights unknown --creator "Source creator" --tags "sfx,comedy" --source-url "https://www.instagram.com/reel/<id>/" --source-start <seconds> --source-end <seconds> --source-sha256 <source-hash> --effect-review pending
```

The `reference-only` status blocks reuse when rights are unknown or the effects-only listening review is pending or failed. After rights and isolation are confirmed, use `library.py --library $stock review --id <stock-id> --rights permission --effect-review passed --note "<listening and permission evidence>"` to update the existing entry. This records a human decision, not an automatic speech-removal result. Do not index a cut containing audible voice as an effect. The four Reel WAVs remain on this machine under `assets/media/sfx/` and are absent from the public Git history.

## Shot-aware sound-effect selection

After listening to an effect, add its audible identity and the kinds of shots where it fits. Use short lowercase slug tags such as `phone-activity`, `comic-payoff`, or `physical-reaction`; these describe the edited shot, not a claim that the Reel source is licensed. Record the editor's identification in the note. The asset catalogue shows the resulting sound profile.

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock describe-sfx --id <stock-id> --label "Digital beep" --shot-tags phone-activity --note "Editor listened to the isolated effect" --identification-review passed
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock list --kind sfx --tag phone-activity
```

Create a shot manifest from the **edited video**, using verified shot boundaries and situation tags. Each shot needs `id`, `start_seconds`, `end_seconds`, `shot_tags`, and `audio_context` (`quiet`, `dialogue`, `music`, or `natural`). The selector proposes only effects with a passed audible-identity review that fit the available shot; it skips dialogue and natural sound. It returns no candidate when tags or duration do not fit. Use the default `pending` identification state when the sound is still unclear. It does not detect shot meaning from video automatically; the editor or an approved understanding pass supplies the tags.

```json
{"schema_version":1,"shots":[{"id":"S01","start_seconds":2.0,"end_seconds":3.0,"shot_tags":["phone-activity"],"audio_context":"quiet"}]}
```

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library $stock suggest-sfx --shots <shot-manifest.json> --output <proposal.json> --mode delivery
```

`delivery` is the default mode and excludes `reference-only` effects. `--mode reference` allows private comparison proposals for uncleared effects; each such candidate has `placement_allowed: false`. Every proposal has `approval_required: true` and `timeline_changed: false`. A Content Studio workflow can run the command as a step bound to its approved precheck plan and save the JSON for cue review. The workflow must not convert a reference proposal into a timeline `sfx` cue; place a reusable effect only after rights, effects-only review, shot timing, and final audio mix are approved. This selector does not render or insert audio.

The separate [memes catalogue](../memes/README.md) handles user-supplied reaction material and scene-based insertion proposals. A self-created meme can be kept here as reusable stock; insertion into a video still goes through the meme skill's contextual review or an approved timeline.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `cta-variants` | Supported | Named design, size, rate, duration, placement → silent transparent ProRes clip | No | [Animated variants](#like--share--subscribe-cta) and [exact-asset review notes](previews/cta-variants.md) | Full asset production follows the approved Content Studio precheck; the generic delivery timeline cannot yet compose this alpha clip. |
| `authored-assets` | Supported | Reviewed visual assets or SFX reference and provenance → Git catalogue and local-only SFX WAVs | No | [Importer tests](tests/test_stock_library.py) | Unknown-rights or unreviewed SFX are reference-only; contextual meme insertion remains in the memes skill. |
| `shot-sfx-select` | Supported | Reviewed sound profiles + edited-shot tags → ranked JSON cue proposals | Proposal only | [Selection tests](tests/test_stock_library.py) | Exact tag and duration matching; unknown-rights effects are reference-only, no automatic timeline insertion. |
