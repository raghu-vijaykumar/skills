# Illustrative engineering scene and render

The [six-second GIF](illustrative-cpu.gif) comes from the actual
`engineering_blender.py` renderer and the checked-in synthetic assembly JSON.
The local run used Blender 4.5.15 LTS, downloaded from the
[official portable release directory](https://download.blender.org/release/Blender4.5/)
and verified against its published SHA-256 file. The gallery builder uses a
temporary 640×360, 12 fps copy of the scene specification and creates the GIF
from its 72-frame MP4:

```powershell
python content-studio/skills/content-studio-video/animation/engineering-3d/previews/build_gallery.py --blender <path-to-blender-4.x>
```

The checked-in `examples/illustrative-cpu-assembly.json` is synthetic geometry.
The temporary MP4 stays under `tmp/capability-gallery/engineering-3d/`; only
the small GIF is committed. The unmodified source specification can also be
rendered directly with:

```powershell
blender -b --python content-studio/skills/content-studio-video/animation/engineering-3d/scripts/engineering_blender.py -- content-studio/skills/content-studio-video/animation/engineering-3d/examples/illustrative-cpu-assembly.json <preview.mp4>
```

The observed result is a cuboid assembly with separation, highlight/opacity
events, and a camera dolly. It is not a faithful CPU interior. Production use
still needs an approved precheck and a review of the exact rendered output.
