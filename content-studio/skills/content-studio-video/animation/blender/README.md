# Headless Blender gallery

The [video animation skill](../SKILL.md) indexes 94 upstream subject and style names for planning. `Catalogued` in the root README does not imply a tested renderer. These three gallery examples are original, explicitly authored Blender scenes. A project can replace their builders while retaining the same preview and full-shot contract.

| Showcase | Builder | Specification | Rendered GIF |
| --- | --- | --- | --- |
| Realistic clamp | [Source](examples/clamp.py) | [Inputs](examples/clamp.json) | [GIF](previews/clamp.gif) |
| Cel character | [Source](examples/character.py) | [Inputs](examples/character.json) | [GIF](previews/character.gif) |
| Atmospheric corridor | [Source](examples/corridor.py) | [Inputs](examples/corridor.json) | [GIF](previews/corridor.gif) |

The [render review](review.md) records the exact encoded assets, hashes, sampled frames, and limits behind these GIFs.

New routes use the [version 2 shot contract](shot-contract.md) for object and beat IDs, rights, and exact render settings. The original three gallery specs remain readable under the version 1 contract.

## Score and select output artifacts

Treat every full MP4 intended for this gallery as a candidate. Inspect its first, action, and held frames and its complete motion; verify frame count, dimensions, required objects, source hashes, and GIF decode. Record **every candidate**, including rejected ones, in [scores.json](scores.json) with its MP4/GIF hashes, technical result, five 0–5 editorial scores, reviewer, and reason. The weighted score covers subject fidelity (25%), motion readability (25%), composition (20%), finish (20%), and evidence integrity (10%). These are editorial review scores, not audience metrics or production approval.

Select the highest-scoring candidate that passes technical review and scores at least 70/100. Commit only that candidate's optimized GIF in `previews/`; retain rejected candidates' scores and hashes. `catalog.py` rejects a `Rendered` claim if its selected GIF is missing, changed, unscored, or outranked. From the repository root, run `python content-studio/skills/content-studio-video/animation/blender/scripts/catalog.py scores` to inspect the current winners before updating the README.

## Rebuild the showcases

From the repository root, replace `<name>` with `clamp`, `character`, or `corridor` and use a new output directory for each preview:

```powershell
$skill = 'content-studio/skills/content-studio-video/animation/blender'
$preview = 'content-studio/skills/content-studio-video/animation/engineering-3d/scripts/headless_preview.py'
$blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $blender) { $blender = 'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe' }
& $blender --background --factory-startup --python-exit-code 1 --python $preview -- --builder "$skill/examples/<name>.py" --input "$skill/examples/<name>.json" --dependency "$skill/examples/common.py" --out "tmp/<name>-frames" --frame 1 --frame 48 --frame 96 --size 1280 720
& $blender --background --factory-startup --python-exit-code 1 --python "$skill/scripts/render_shot.py" -- --builder "$skill/examples/<name>.py" --input "$skill/examples/<name>.json" --dependency "$skill/examples/common.py" --out "tmp/<name>.mp4"
ffmpeg -hide_banner -loglevel error -y -i "tmp/<name>.mp4" -vf "fps=8,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" -loop 0 "$skill/previews/<name>.gif"
```

The generated report records the exact Blender version, input and output hashes, resolution, and encoded frame count. Inspect action timing and detail in the full MP4. The GIFs in the root README are compressed review copies of those renders; they do not replace the full motion and structural checks.

For a long shot, add `--resumable --batch-frames 48` to the full-shot command. It records hashed PNGs and a durable log beside the output, checks free space before each batch, and writes `complete.json` only after probing the encoded MP4. Repeat the same command and output path after an interruption; changed inputs or cached frames fail closed. `--stop-after 1` is available for a bounded pause and resume test. The [resumable render review](resume-review.md) records a real stop, resume, and uninterrupted comparison.

For a Content Studio video, copy the approved MP4 into the project asset folder, record its project-relative path and SHA-256 in `asset-manifest.json` with `origin: "procedural"`, and place it in the storyboard or Remotion scene at the intended narration cue. Use the [videogen asset contract](../videogen/references/idea-to-explainer.md) and review the hero alone, in the narrated composition, and in the exact final render. Real drafts must complete the [workflow precheck](../../../content-studio-workflow/SKILL.md) and obtain approval of the current production plan before editing. The edited-video delivery timeline does not yet consume Blender shot operations directly.
