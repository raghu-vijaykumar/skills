# Transition catalog and review guide

Source: [20 video transitions that transform video editing](https://clipchamp.com/en/blog/video-transitions-transform-video-editing/)
(Microsoft Clipchamp, updated 2025-10-22). The article describes the effects;
this skill maps them to FFmpeg where a faithful or clearly labelled
approximation exists.

## Fidelity labels

| Label | Meaning |
| --- | --- |
| `native` | A direct FFmpeg `fade` or `xfade` mapping with the intended motion. |
| `approximate` | A rendered effect that is visibly related but not identical to the Clipchamp asset. |
| `catalog-only` | Reserved for a future entry without a renderer; none of the current 29 entries has this label. |

## Catalog

| Article | ID | Name | Modes | Fidelity | Renderer |
| --- | --- | --- | --- | --- | --- |
| 1 | `burn` | Burn | point | approximate | orange dip |
| 2 | `horizontal-banding` | Horizontal banding | join | approximate | `hlwind` |
| 3 | `diagonal-soft-wipe` | Diagonal soft wipe | join | approximate | `diagtl` |
| 4 | `blinds` | Blinds | join | approximate | `hlslice` |
| 5 | `bloom` | Bloom | join | approximate | `zoomin` |
| 6 | `collage` | Collage | join | approximate | custom staggered panels |
| 7 | `pixelate` | Pixelate | join | native | `pixelize` |
| 8 | `exchange` | Exchange | join | approximate | `slideleft` |
| 9 | `page-turn` | Page turn | join | approximate | custom shaded 2D fold |
| 10 | `reveal` | Reveal | join | native | `revealleft` |
| 11 | `liquid-streaks` | Liquid streaks | join | approximate | custom wavy edge |
| 11 | `liquid-drops` | Liquid drops | join | approximate | custom expanding pools |
| 12 | `fade-through-black` | Fade through black | point, join | native | `fade` / `fadeblack` |
| 12 | `fade-through-white` | Fade through white | point, join | native | `fade` / `fadewhite` |
| 13 | `fire` | Fire | join | approximate | custom warm flame-shaped edge |
| 14 | `glitch` | Glitch | point | approximate | RGB shift + noise |
| 14 | `glitch-reveal` | Glitch reveal | point | approximate | RGB shift + noise + contrast |
| 15 | `zoom-in` | Zoom in | join | native | `zoomin` |
| 15 | `zoom-out` | Zoom out | join | approximate | custom outgoing shrink |
| 16 | `spin` | Spin | join | approximate | custom rotating outgoing frame |
| 17 | `heart` | Heart | join | approximate | custom growing heart mask |
| 18 | `wipe-right` | Wipe right | join | native | `wiperight` |
| 18 | `wipe-left` | Wipe left | join | native | `wipeleft` |
| 19 | `cross-blur` | Cross blur | point, join | native | `gblur` / `hblur` |
| 19 | `cross-fade` | Cross fade | join | native | `fade` |
| 20 | `push-left` | Push left | join | native | `slideleft` |
| 20 | `push-right` | Push right | join | native | `slideright` |
| 20 | `push-up` | Push up | join | native | `slideup` |
| 20 | `push-down` | Push down | join | native | `slidedown` |

The article's introduction also names fade-out, pan, jump cuts, swipe, and
cross-dissolve. The numbered catalog covers them: fade-out maps to
`fade-through-black`/`fade-through-white`, swipe to `wipe-left`/`wipe-right`,
cross-dissolve to `cross-fade`, and pan to the `push-*` family. A jump cut is a
hard cut, not a rendered transition, so it needs no entry here.

## Per-transition scripts

Each transition ID has a fixed entrypoint at `scripts/<id with hyphens replaced
by underscores>.py`; `transitions.py scripts` prints the mapping. Each script
fills in its own `id` when a cue omits it and rejects a cue that names a
different transition. Point sheets go to the point renderer; a sheet with an
`inputs` array goes to the join renderer. `--mode` overrides the detection and
`--plan` resolves without rendering.

```bash
python .../scripts/fade_through_black.py cues.json --input master.mp4 --output out.mp4
python .../scripts/push_left.py cues.json --output joined.mp4
```

The eight custom effects have the same fixed-entrypoint contract and require a
two-input join sheet. The shared `transitions.py apply` and
`transitions.py join` commands remain the way to mix IDs in one cue sheet.

## Point vs join

`apply` writes a time-preserving effect on one master. A fade is a coloured
RGBA overlay whose alpha ramps up and back down, so the rest of the master is
untouched; blur and glitch use timeline-enabled `gblur`, `rgbashift`, `noise`,
and `eq`. The output keeps the input duration and audio can be stream-copied.

`join` builds an `xfade` chain across ordered clips. Each boundary consumes its
transition duration, so the result is shorter by the sum of the durations. The
command prints `output_seconds` and `duration_change_seconds`; never hide that
change.

Custom joins use original per-pixel expressions over both clips. They are
rendered directly in the join graph, including the delivery timeline's single
final export. The results approximate the named visual ideas; no proprietary
or filmed motion asset is present. Normalize source color to SDR before using
these effects. Review entrance, midpoint, and exit frames and motion at the
intended delivery size.

## Cue semantics

- `at` is the centre of the effect in the master timeline, in seconds.
- `duration` is the full effect length. Defaults come from `presets/transitions.json`.
- Point cues may not overlap. Leave at least 0.05 s between them.
- A point cue must fit inside the master; a join transition must be shorter than
  both neighbouring clips.
- `after` in a join sheet is the zero-based index of the clip before the boundary.

## Choosing a transition

| Intent | Prefer | Avoid |
| --- | --- | --- |
| Calm vlog beat | `cross-fade`, `fade-through-black` | `glitch`, `pixelate` |
| Location change | `wipe-left`, `push-left`, `reveal` | a long dissolve |
| Comparison / before-after | `push-left`, `push-right`, `exchange` | `heart` |
| Action or gaming beat | `pixelate`, `zoom-in`, `glitch` | a slow fade |
| Reveal or suspense | `fade-through-black`, `diagonal-soft-wipe` | a busy wipe |
| Retro / tech | `horizontal-banding`, `blinds`, `scanline` assets | a romantic fade |

The article's own guidance applies: there is no fixed limit on how many
transitions to use, but leave enough time and space for the audience to
appreciate the content, and match transitions with sound effects only when the
edit already has a sound design.

## Review checklist

1. Sample the entrance, midpoint, and exit of every transition at delivery size.
2. Confirm the transition does not cover a face, food, landmark, or on-screen text.
3. For `apply`, confirm total duration is unchanged and narration is in sync.
4. For `join`, confirm each boundary, the audio crossfade, and the duration change.
5. Check that the effect serves the beat; remove it if it draws more attention
   than the shot.
6. Keep the cue sheet, output, and any preview together. Preserve the source.

## Limits

- The custom eight are code-generated approximations, so a project seeking a
  physical page curl, filmed fire, or liquid footage still needs a separately
  sourced asset and its own reviewed render route.
- No automatic cut detection or auto-placement.
- HDR/HLG and BT.2020 are refused; tone-map to SDR first. Dolby Vision is unsupported.
- The native timeline renderer does not consume `point_transitions` annotations yet.
- Transition sound effects and music are out of scope.
