# Headless Blender previews

Use a working Blender executable and a new output folder. The assembly renderer supports Blender 4.2 or later. Pick initial, moving, and settled frames at the eventual delivery resolution. Use several warm frames to estimate cost. Record fragile GPU settings and benchmark the most complex scene before projecting a full render.

The project Python builder exposes `make_scene(spec, spec_dir)` and returns a `bpy.types.Scene` with a camera, frame range, and media settings. Generate or import geometry and author the animation in that function. Resolve paths relative to `spec_dir`. Use only trusted scene code and its authored dependencies.

```powershell
# Run from the engineering-3d skill directory. Use an absolute executable if needed.
blender --background --factory-startup --python-exit-code 1 --python scripts/headless_preview.py -- --builder scripts/engineering_blender.py --input examples/illustrative-cpu-assembly.json --out review/assembly-frames --frame 1 --frame 36 --frame 72 --size 1280 720
```

- Point `--builder` at a project file for scripted joints, pivots, motion paths, labels, and cameras. Use `--required-object` for each part ID that must exist and `--dependency` to fingerprint imported meshes, textures, or helper files.
- Repeat `--frame` for representative states. Use `--range 20 49` for a short continuous segment when reviewing the action at the scene’s frame rate with FFmpeg. The range includes both endpoints.
- Inspect `preview.json` for Blender version, engine, frame rate, dimensions, input and rendered file hashes, first-frame time, later-frame median, and sample sizes. Budget working storage for one shot or batch at a time when a whole film’s decoded image sequence would take too much space.
- Review the generated pictures for contact, clearance, readability, and accurate motion. Compare equivalent states using [video critique](../../../review/critique/SKILL.md), then check the narrated master.
