# Reusable vlog effects and transitions

## Finished video

`effect` cues use source-video seconds. Their midpoint is the peak: `flash` is brightest, `swipe` covers the frame, and `shutter` closes. Put an existing hard cut at that midpoint when the effect is meant to conceal it. `speed-lines` and `frame-pop` emphasize a moment without replacing footage. Defaults are neutral teal, warm cream, and amber; `color` and `accent` accept `#RRGGBB` values.

The cut-cover presets require at least 0.30 seconds; use roughly 0.4–0.8 seconds for a deliberate beat. Their full-cover hold spans the midpoint so frame sampling cannot expose a thin seam at the cut. Action accents can be shorter, but must last at least 0.18 seconds.

```json
{
  "source": "C:/path/to/edited-vlog.mp4",
  "events": [
    {"kind": "effect", "preset": "flash", "start": 12.8, "end": 13.2},
    {"kind": "effect", "preset": "swipe", "start": 24.7, "end": 25.3,
     "color": "#106A60", "accent": "#FFB54A"},
    {"kind": "effect", "preset": "shutter", "start": 40.7, "end": 41.3},
    {"kind": "effect", "preset": "speed-lines", "start": 52.0, "end": 52.5},
    {"kind": "effect", "preset": "frame-pop", "start": 61.2, "end": 61.8}
  ]
}
```

Run `python scripts/overlay.py validate <cues.json>`, then `sidecar <cues.json> --output <source-basename.ass>`. Load the ASS over the original for the exact source video and audio. `render <cues.json> --start S --duration D --output <new-preview.mp4>` makes a bounded review copy. A Dolby Vision source requires `--allow-dv-preview`: the combined copy preserves the HLG base-layer tags, not its RPU. Never overwrite the original or describe the preview as Dolby Vision equivalent. Review the entrance, midpoint, and exit of each cue at delivery size; a still at the peak does not establish whether the motion feels right. The ASS canvas follows the source aspect ratio, including portrait footage.

Silent source clips are supported: the preview keeps them silent. When audio exists, it is copied from the source.

The overlay colors are authored as RGB graphics and may look different under an HDR player's display transform. Check them on the intended display; this does not imply a grade or color transform to the source footage.

## Remotion vlog

The package exports `VlogEffect` and `VlogTransition` from `@raghu-vijaykumar/videogen/runtime/vlogEffects`. Mount each component inside a `Sequence` whose local frame 0 starts the effect. Choose `durationInFrames` equal to the Sequence length.

```tsx
import {Sequence} from 'remotion';
import {VlogEffect, VlogTransition} from '@raghu-vijaykumar/videogen/runtime/vlogEffects';

<Sequence from={90} durationInFrames={18}>
  <VlogEffect preset="swipe" durationInFrames={18} color="#106A60" />
</Sequence>

<Sequence from={180} durationInFrames={18}>
  <VlogTransition preset="wipe" durationInFrames={18}
    from={<OutgoingShot />} to={<IncomingShot />} />
</Sequence>
```

`VlogTransition` also supports `crossfade`, `slide`, and `flash`, plus `direction="left"|"right"` for slide and wipe. It mixes the two visual scene nodes only; supply their video frames for the whole transition interval and handle audio crossfades separately. Keep the scenes mounted outside the transition interval as needed. The progress reaches 0 on the first frame and 1 on the last, so the next scene can begin without a visual seam. Avoid full-frame flash or shutters over important faces or food details unless that interruption serves the edit.
