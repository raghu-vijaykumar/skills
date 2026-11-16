---
name: content-studio-video-engineering-3d
description: Render approved engineering assets and authored Blender event timelines.
---

# content-studio-video-engineering-3d

Use the [code-first 3D workflow](references/code-first-explainer.md) for a mechanism explainer that starts from an idea or a reference video. Carry stable IDs from the timed storyboard into the model sources, scene code, and critique evidence.

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Use `scripts/model_assets.py` to import approved geometry and `scripts/engineering_blender.py` for assembly separation and supported events from `scripts/engineering_timeline.py`. Author project-specific `bpy` code for other motion and validate its headless render separately. The CPU example uses illustrative geometry. Preview the hero and detail ranges, then verify the narrated delivery render.
