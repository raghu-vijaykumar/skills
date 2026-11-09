# Illustrative engineering scene (not a render)

Blender is not installed in the matrix-evidence environment, so no rendered clip is
committed. This is a reproducible command and input example, not renderer evidence.

```powershell
blender -b --python content-studio/skills/content-studio-video/animation/engineering-3d/scripts/engineering_blender.py -- content-studio/skills/content-studio-video/animation/engineering-3d/examples/illustrative-cpu-assembly.json preview.mp4
```

The checked-in `examples/illustrative-cpu-assembly.json` is synthetic geometry. The
run writes one preview MP4 at the requested path. Review a hero frame, a detail
range, and the authored component/camera timeline before using the output.

Expected result: a short cuboid assembly animation with exploded/assembled states,
highlight and opacity events, and a dolly camera. It is not a faithful CPU interior.
