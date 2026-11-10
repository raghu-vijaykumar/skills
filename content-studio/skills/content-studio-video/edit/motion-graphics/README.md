# Motion graphics capability matrix

Add reusable timed motion graphics and transition effects to an edited video, or use
matching components in a Remotion vlog. The committed GIF is a real overlay render of
all five finished-video effects on a synthetic source.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `presets` | Supported | Category + preset ID + proposed cues → resolved preset JSON + cue validation | Specialist only | [Effect preview](previews/effects.gif) | Style specification and validation layer, not proof every preset animation is rendered by overlay.py. |
| `overlay` | Supported | Cue sheet + edited source → bounded review MP4 or ASS sidecar | Specialist only | [Effect preview](previews/effects.gif) | Cooking/location card types; source untouched; Dolby Vision preview loses RPU. |
| `cta-stock` | Supported | Compatibility command → silent transparent UHD ProRes 4444 MOV | No | [CTA example](previews/cta-stock.md) | Canonical designs and selection are in the [stock library](../../stock-library/README.md). |
| `hdr-compose` | Supported | Versioned manifest + hashes + human approval → HEVC Main10 HLG-base master | No | [HLG example](previews/hdr-compose.md) | Narrow 3840x2160/30 route; five-second intro/CTA; no Dolby Vision RPU preservation. |

## Named presets

Select a preset through `presets.py`; this is a style specification and cue-validation
layer, not a claim that every animation is rendered by `overlay.py`. The nine presets are:

| Category | Presets | Default |
| --- | --- | --- |
| travel | `travel-cinematic`, `travel-playful`, `travel-journal` | `travel-cinematic` |
| cooking | `cooking-recipe`, `cooking-minimal`, `cooking-playful` | `cooking-recipe` |
| daily | `daily-clean`, `daily-playful`, `daily-cozy` | `daily-clean` |

The finished-video effect presets are `flash`, `swipe`, `shutter`, `speed-lines`, and
`frame-pop`. The [effect GIF](previews/effects.gif) shows all five rendered on a
synthetic source. Remotion exports `VlogEffect` and `VlogTransition` separately.


## Evidence note

The GIF is rendered by `overlay.py` from a synthetic cue sheet. Preset JSON is a
specification layer; the CTA and HLG routes are labelled command examples because
their outputs are large or manifest-bound. No private footage or full master is included.

For reusable CTA designs, select `classic-bar`, `minimal-pills`, or `bold-stack` in the [stock library catalogue](../../stock-library/README.md). This skill owns timed placement and the narrow HLG composition route; the old `cta_stock.py` command delegates to the stock library generator.
