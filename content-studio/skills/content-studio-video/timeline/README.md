# Delivery timeline capability matrix

Plan, validate, approve, and render an immutable delivery timeline. The committed GIF
and validation output are real `init -> validate -> preview` results from a synthetic
source; the fixture approval is synthetic and is not a production approval.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `timeline-delivery` | Supported | Approved timeline + hashed sources/voice/fonts/sidecars + human approval → one final MP4 + render record | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Approval must match the exact revision and input bytes; SDR only. |
| `crop` | Supported | Timeline picture clip + crop geometry → cropped picture in final render | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Editable per clip; preview affected ranges. |
| `lens-correction` | Supported | Timeline clip + lens parameters → lens-corrected picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Explicit parameters; no automatic camera profile. |
| `denoise-light` | Supported | Timeline clip range → denoised picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Light denoise only; no detail reconstruction. |
| `denoise-medium` | Supported | Timeline clip range → denoised picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Stronger smoothing; inspect texture. |
| `deflicker` | Supported | Timeline clip range → deflickered picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Temporal flicker only. |
| `upscale-lanczos` | Supported | Timeline clip range → Lanczos-scaled picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Resolution scaling only; AI upscale is not in this route. |
| `color-eq` | Supported | Timeline clip/operation → basic color EQ | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Built-in EQ only; no LUT import or full preset catalog. |
| `sharpen-light` | Supported | Timeline clip/operation → sharpened picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Cannot recover missed focus. |
| `sharpen-medium` | Supported | Timeline clip/operation → sharpened picture | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Halo/noise risk; review at delivery size. |
| `title` | Supported | Timeline operation + text/font → burned-in title | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Needs drawtext/font support; does not invent titles. |
| `highpass` | Supported | Timeline audio cue → high-passed audio | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | 80 Hz-style dialogue cleanup only. |
| `audio-denoise` | Supported | Timeline audio cue → denoised audio | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Basic filter; subjective result needs listening. |
| `compress` | Supported | Timeline audio cue → compressed audio | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Gentle dialogue compression only. |
| `loudnorm` | Supported | Timeline audio cue → loudness-normalized audio | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | One-pass approximation; measure and listen. |
| `cross-fade` | Supported | Editable join cue + adjacent picture → Cross fade in the final render | Yes | [Cross fade preview](../edit/transitions/previews/cross-fade.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `fade-through-black` | Supported | Editable point or join cue + adjacent picture → Fade through black in the final render | Yes | [Fade through black preview](../edit/transitions/previews/fade-through-black.gif) | Native point or join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `fade-through-white` | Supported | Editable point or join cue + adjacent picture → Fade through white in the final render | Yes | [Fade through white preview](../edit/transitions/previews/fade-through-white.gif) | Native point or join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `cross-blur` | Supported | Editable point or join cue + adjacent picture → Cross blur in the final render | Yes | [Cross blur preview](../edit/transitions/previews/cross-blur.gif) | Native point or join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `burn` | Supported | Editable point cue + adjacent picture → Burn in the final render | Yes | [Burn preview](../edit/transitions/previews/burn.gif) | Approximate point transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `glitch` | Supported | Editable point cue + adjacent picture → Glitch in the final render | Yes | [Glitch preview](../edit/transitions/previews/glitch.gif) | Approximate point transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `glitch-reveal` | Supported | Editable point cue + adjacent picture → Glitch reveal in the final render | Yes | [Glitch reveal preview](../edit/transitions/previews/glitch-reveal.gif) | Approximate point transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `horizontal-banding` | Supported | Editable join cue + adjacent picture → Horizontal banding in the final render | Yes | [Horizontal banding preview](../edit/transitions/previews/horizontal-banding.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `diagonal-soft-wipe` | Supported | Editable join cue + adjacent picture → Diagonal soft wipe in the final render | Yes | [Diagonal soft wipe preview](../edit/transitions/previews/diagonal-soft-wipe.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `blinds` | Supported | Editable join cue + adjacent picture → Blinds in the final render | Yes | [Blinds preview](../edit/transitions/previews/blinds.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `bloom` | Supported | Editable join cue + adjacent picture → Bloom in the final render | Yes | [Bloom preview](../edit/transitions/previews/bloom.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `pixelate` | Supported | Editable join cue + adjacent picture → Pixelate in the final render | Yes | [Pixelate preview](../edit/transitions/previews/pixelate.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `exchange` | Supported | Editable join cue + adjacent picture → Exchange in the final render | Yes | [Exchange preview](../edit/transitions/previews/exchange.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `reveal` | Supported | Editable join cue + adjacent picture → Reveal in the final render | Yes | [Reveal preview](../edit/transitions/previews/reveal.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `zoom-in` | Supported | Editable join cue + adjacent picture → Zoom in in the final render | Yes | [Zoom in preview](../edit/transitions/previews/zoom-in.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `push-up` | Supported | Editable join cue + adjacent picture → Push up in the final render | Yes | [Push up preview](../edit/transitions/previews/push-up.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `push-down` | Supported | Editable join cue + adjacent picture → Push down in the final render | Yes | [Push down preview](../edit/transitions/previews/push-down.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `collage` | Supported | Editable join cue + adjacent picture → Collage in the final render | Yes | [Collage preview](../edit/transitions/previews/collage.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `page-turn` | Supported | Editable join cue + adjacent picture → Page turn in the final render | Yes | [Page turn preview](../edit/transitions/previews/page-turn.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `liquid-streaks` | Supported | Editable join cue + adjacent picture → Liquid streaks in the final render | Yes | [Liquid streaks preview](../edit/transitions/previews/liquid-streaks.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `liquid-drops` | Supported | Editable join cue + adjacent picture → Liquid drops in the final render | Yes | [Liquid drops preview](../edit/transitions/previews/liquid-drops.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `fire` | Supported | Editable join cue + adjacent picture → Fire in the final render | Yes | [Fire preview](../edit/transitions/previews/fire.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `zoom-out` | Supported | Editable join cue + adjacent picture → Zoom out in the final render | Yes | [Zoom out preview](../edit/transitions/previews/zoom-out.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `spin` | Supported | Editable join cue + adjacent picture → Spin in the final render | Yes | [Spin preview](../edit/transitions/previews/spin.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `heart` | Supported | Editable join cue + adjacent picture → Heart in the final render | Yes | [Heart preview](../edit/transitions/previews/heart.gif) | Approximate join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `wipe-left` | Supported | Editable join cue + adjacent picture → Wipe left in the final render | Yes | [Wipe left preview](../edit/transitions/previews/wipe-left.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `wipe-right` | Supported | Editable join cue + adjacent picture → Wipe right in the final render | Yes | [Wipe right preview](../edit/transitions/previews/wipe-right.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `push-left` | Supported | Editable join cue + adjacent picture → Push left in the final render | Yes | [Push left preview](../edit/transitions/previews/push-left.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `push-right` | Supported | Editable join cue + adjacent picture → Push right in the final render | Yes | [Push right preview](../edit/transitions/previews/push-right.gif) | Native join transition; editable 0.15-3 s; changed recipe needs fresh approval. |
| `upscale-real-esrgan` | Unsupported | Timeline clip → not available in this route | No | [Validation](previews/validate.txt) | Unsupported: AI upscale needs a separate adapter and evidence. |
| `upscale-pytorch` | Unsupported | Timeline clip → not available in this route | No | [Validation](previews/validate.txt) | Unsupported: AI upscale needs a separate adapter and evidence. |
| `motion-graphics-ass` | Supported | Timeline operation + approved ASS sidecar → rendered motion graphics in final | Yes | [Timeline preview](previews/timeline-preview.gif) and [validation](previews/validate.txt) | Consumes approved ASS sidecars; not every motion-graphics preset. |
| `hdr-dolby-vision` | Unsupported | HDR/Dolby Vision timeline → not available in this route | No | [Validation](previews/validate.txt) | Unsupported: the delivery timeline is SDR-only. |

## Route limits

- The timeline is one SDR export from an approved revision; it is not a claim that every
  specialist preview is delivery-equivalent.
- AI upscale, HDR/Dolby Vision, and the three unsupported IDs above stop validation.
- Point transitions live in `operations`; two-shot joins live in `transitions`.
- A changed timeline, source, voice, font, sidecar, plan, or renderer capability
  invalidates prior approval.

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
