# Delivery-timeline method previews

These are **actual outputs of `model.validate` and `compiler.preview`** from
synthetic two-second sources. The local fixture plan and checklist serve only
this gallery. Its approval record is explicitly synthetic, with no human
actor; these are bounded previews, not production renders or editor approval.
The frame comparisons show source on the left and the timeline preview on the
right. Each effect occupies 0–2 seconds in an editable operation. Run from the
repository root:

```powershell
python content-studio/skills/content-studio-video/timeline/previews/build_methods.py
```

The script creates `tmp/capability-gallery/timeline/` inputs and short MP4s,
then writes the small JPEG, GIF, and MP3 examples in `previews/methods/`.
It uses FFmpeg testsrc2 (SMPTE bars for the title), generated tones/noise,
Arial for text, and a synthetic ASS sidecar. It calls the same timeline
validator and FFmpeg graph compiler as
the delivery renderer. Final delivery still needs an actual approved plan,
reviewed timeline revision, and separate human timeline approval.

| Timeline operation | Actual example | Input and parameter | Review limit |
| --- | --- | --- | --- |
| `crop` | [Before / after](methods/crop.jpg) | Test pattern; normalized x=.16, y=.12, w=.68, h=.76 | Geometry only; content framing needs editor review. |
| `lens-correction` | [Before / after](methods/lens-correction.jpg) | Test pattern; k1=.3, k2=.05 | Deliberately strong synthetic distortion; no camera calibration. |
| `denoise-light` | [Before / after](methods/denoise-light.jpg) | Spatial/temporal noise 25; hqdn3d light | Compare fine detail in real footage before choosing. |
| `denoise-medium` | [Before / after](methods/denoise-medium.jpg) | Same noisy source; hqdn3d medium | More smoothing may remove texture. |
| `deflicker` | [Animated before / after](methods/deflicker.gif) | Four-frame synthetic brightness pulse; deflicker mode pm, size 10 | Loop shows temporal behavior; effectiveness varies with real flicker. |
| `upscale-lanczos` | [Before / after](methods/upscale-lanczos.jpg) | 160×90 source on 320×180 canvas; 2× Lanczos | Scaling choice, not new detail or AI upscale. |
| `color-eq` | [Before / after](methods/color-eq.jpg) | Contrast 1.3, brightness .08, saturation 1.4 | Example settings, not an approved look. |
| `sharpen-light` | [Before / after](methods/sharpen-light.jpg) | `cas` strength .25 | Effect is subtle; check texture and noise at output size. |
| `sharpen-medium` | [Before / after](methods/sharpen-medium.jpg) | `cas` strength .45 | Watch for halos and amplified noise. |
| `title` | [Before / after](methods/title.jpg) | Arial and “TIMELINE TITLE” | Font is a hashed input in a real timeline. |
| `motion-graphics-ass` | [Before / after](methods/motion-graphics-ass.jpg) | Synthetic ASS line “TIMELINE GRAPHIC” | Proves sidecar consumption, not every motion-graphics preset. |
| `highpass` | [Before](methods/highpass-before.mp3) / [after](methods/highpass-after.mp3) | 60 Hz rumble plus 440 Hz tone; default 80 Hz highpass | Artificial tone, not speech cleanup approval. |
| `audio-denoise` | [Before](methods/audio-denoise-before.mp3) / [after](methods/audio-denoise-after.mp3) | 440 Hz tone plus synthetic white noise; `afftdn` | Highpassed 3–12 kHz mean level fell from −36.8 to −48.3 dB; listen for speech damage on real material. |
| `compress` | [Before](methods/compress-before.mp3) / [after](methods/compress-after.mp3) | Level-modulated 440 Hz tone; 2:1 compressor | Loud passages reduce; real dialogue needs listening review. |
| `loudnorm` | [Before](methods/loudnorm-before.mp3) / [after](methods/loudnorm-after.mp3) | Low-level 440 Hz tone; target −16 LUFS, −1.5 dBTP | One-pass approximation; measure delivered audio. |

`audio-denoise` high-band values are a bounded measurement of the encoded
gallery MP3s using FFmpeg `highpass=f=3000,volumedetect`; they are not a
quality score for dialogue. No source media or temporary MP4 is committed.
