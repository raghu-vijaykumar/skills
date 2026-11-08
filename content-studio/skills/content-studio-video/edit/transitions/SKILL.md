---
name: content-studio-video-transitions
description: Choose and apply reviewed video transitions at timeline points or clip joins.
---

# Video transitions

Before changing the draft, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist. Read the source edit, sample the affected ranges, and agree on transition IDs, exact timestamps, durations, output path, fallback, and review criterion.

This skill owns transition choice and application. It extends [motion graphics](../motion-graphics/SKILL.md), which draws overlays over footage, and [clip edit](../clip-edit/SKILL.md), which trims and joins. It does not replace either.

## Two routes

- **Point transition** (`apply`): a time-preserving effect at a timestamp on one finished master. Total duration and narration stay unchanged. Use this for a dip, blur, glitch, or burn inside a continuous edit.
- **Clip join** (`join`): an `xfade` between ordered clips. The overlap shortens the result, so the tool reports the exact duration change. Use this for wipes, pushes, slides, and dissolves at real cuts.

Wipes, pushes, slides, and spins need two shots. Do not fake them by splitting one continuous master: the overlap would blend a moment with itself. Use `apply` for point effects and `join` for boundaries.

## Catalog

The catalog covers the 20 sections and 29 variants in the [Clipchamp transitions article](https://clipchamp.com/en/blog/video-transitions-transform-video-editing/). Every entry is labelled `native`, `approximate`, or `catalog-only`.

```bash
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py list
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py list --mode point
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py list --fidelity catalog-only --json
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py scripts
```

`catalog-only` transitions (collage, page turn, liquid streaks/drops, fire, heart, spin, zoom-out) have no renderer here. The tool refuses them with an explicit error; it never emits a placeholder. Use a motion-graphics asset for those instead.

## Per-transition scripts

Every catalog transition has its own entrypoint under `scripts/`. The filename
replaces hyphens with underscores; `transitions.py scripts` prints the exact
mapping.

```bash
# Point: one master, duration unchanged.
python content-studio/skills/content-studio-video/edit/transitions/scripts/fade_through_black.py cues.json --input master.mp4 --output out.mp4

# Join: ordered clips, duration change reported.
python content-studio/skills/content-studio-video/edit/transitions/scripts/push_left.py cues.json --output joined.mp4

# Dual-mode transition: choose the route explicitly when needed.
python content-studio/skills/content-studio-video/edit/transitions/scripts/cross_blur.py cues.json --output joined.mp4 --mode join
```

Each script fixes its transition ID. A cue may omit `id`; the script fills it
in. A cue that names a different transition is rejected, so `push_left.py`
cannot silently render a wipe. Use `--plan` to resolve timings without
rendering.

Catalog-only transitions still have a script, but running it exits with an
explicit refusal instead of emitting a placeholder.

The shared `transitions.py apply` and `transitions.py join` commands remain
available when one cue sheet combines several different transition IDs.

## Apply point transitions

Create a cue sheet in master seconds. `at` is the centre of the effect and `duration` is its full length.

```json
{
  "transitions": [
    {"at": 12.5, "id": "fade-through-black", "duration": 0.8},
    {"at": 40.0, "id": "glitch", "duration": 0.4},
    {"at": 63.2, "id": "cross-blur", "duration": 0.6}
  ]
}
```

```bash
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py validate cues.json --input master.mp4
python content-studio/skills/content-studio-video/edit/transitions/scripts/apply.py cues.json --input master.mp4 --output master-transitions.mp4
python content-studio/skills/content-studio-video/edit/transitions/scripts/apply.py cues.json --input master.mp4 --output preview.mp4 --preview-start 10 --preview-duration 6
```

Point-capable IDs: `fade-through-black`, `fade-through-white`, `cross-blur`, `glitch`, `glitch-reveal`, and `burn` (warm approximation). Keep cues at least 0.05 s apart and inside the master duration.

## Join clips

```json
{
  "inputs": ["a.mp4", "b.mp4", "c.mp4"],
  "transitions": [
    {"after": 0, "id": "cross-fade", "duration": 0.6},
    {"after": 1, "id": "wipe-left", "duration": 0.5}
  ]
}
```

```bash
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py validate cues.json --mode join
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py plan cues.json
python content-studio/skills/content-studio-video/edit/transitions/scripts/join.py cues.json --output joined.mp4
```

`join` normalizes every clip to the largest canvas and the first clip's frame rate, cross-fades audio when every clip has it, and reports `output_seconds` and `duration_change_seconds`. A transition must be shorter than both neighbouring clips.

## Annotate an edit timeline

```bash
python content-studio/skills/content-studio-video/edit/transitions/scripts/transitions.py annotate edit-timeline.json --cues cues.json --output edit-timeline-transitions.json
```

This writes a copy with `point_transitions` on the matching clip. The native timeline renderer does not consume those annotations yet; use `apply` for a supported render.

## Choose well

- Match the transition to mood and pace. A hard cut is still the default; add a transition only when it serves a beat, a location change, or a deliberate reveal.
- Leave breathing room. Do not stack transitions or place them over important speech, faces, food, or text.
- Keep most transitions between 0.3 s and 0.8 s. Anything longer becomes the subject.
- Pair a transition with its sound effect only when the edit already has a sound design; do not add audio here.
- Prefer a simple dissolve or dip for vlogs. Reserve glitch, pixelate, and stylized effects for intentional genre beats.

## Review gates

- Preview the exact affected range, not a still. Check entrance, midpoint, and exit at delivery size.
- For `apply`, confirm the total duration is unchanged and narration is still in sync.
- For `join`, confirm every boundary, the audio crossfade, and the reported duration change.
- Reject a transition that hides a face, food, landmark, or on-screen text, or that draws more attention than the shot.
- HDR/HLG and BT.2020 input is refused; tone-map to SDR first. Dolby Vision is not supported.
- Outputs are always new files. Preserve the source master, cue sheet, and preview together.

## Boundaries

- No motion assets are generated. Catalog-only effects require a separate renderer.
- No automatic transition detection or auto-placement. Every cue is explicit and reviewable.
- No audio effects or transition sound design; audio is only cross-faded on `join`.
- The skill does not publish; publication remains a separate approved request.
