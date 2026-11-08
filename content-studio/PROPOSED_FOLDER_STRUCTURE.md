# Proposed Content Studio folder structure

Status: draft for review and editing. This describes the intended organization, not the current files.

Use one discoverable skill folder per operation type, with a separate script for each method. Skill folders sit directly under `content-studio/skills/` because the current installer links direct children of that directory.

```text
content-studio/
├─ skills/
│  ├─ content-studio/                 # lifecycle router
│  ├─ content-studio-workflow/        # precheck, plan, approval, execution
│  │  ├─ SKILL.md
│  │  ├─ methods.json                 # available operations and method IDs
│  │  ├─ scripts/
│  │  │  ├─ profile.py
│  │  │  ├─ plan.py
│  │  │  ├─ approve.py
│  │  │  └─ run.py
│  │  └─ tests/
│  │
│  ├─ content-studio-ideagen/         # analytics, comparisons, idea planning
│  ├─ content-studio-styles/          # style catalogue
│  ├─ content-studio-style-engine/    # scene plan, storyboard, consistency
│  ├─ content-studio-engineering-3d/  # Blender cutaway method
│  │
│  ├─ content-studio-videopreprocess/ # coordinates approved source operations
│  ├─ content-studio-ingest/
│  │  └─ scripts/{order.py, dedupe.py}
│  ├─ content-studio-blur-review/
│  │  └─ scripts/{detect.py, apply_approved_cuts.py}
│  ├─ content-studio-stabilize/
│  │  └─ scripts/vidstab.py
│  ├─ content-studio-audio-tune/
│  │  └─ scripts/{deepfilter.py, afftdn.py, keep_source.py}
│  │
│  ├─ content-studio-autocut/
│  │  └─ scripts/{heuristic_select.py, transcript_select.py,
│  │              annotation_select.py, render.py, review.py}
│  ├─ content-studio-reframe/
│  │  └─ scripts/{subject_boxes.py, saliency.py, center.py}
│  ├─ content-studio-videoedit/
│  │  └─ scripts/{trim.py, cut.py, join.py}
│  ├─ content-studio-color/
│  │  └─ scripts/{preset.py, lut.py, shot_match.py}
│  ├─ content-studio-upscale/
│  │  └─ scripts/{lanczos.py, real_esrgan.py, compare.py}
│  ├─ content-studio-restoration/
│  │  └─ scripts/{denoise.py, deflicker.py, lens.py, sharpen.py, refine.py}
│  ├─ content-studio-quality/
│  │  └─ scripts/{ssim.py, psnr.py, vmaf.py}
│  ├─ content-studio-benchmark/
│  ├─ content-studio-motion-graphics/
│  │
│  ├─ content-studio-videogen/        # Remotion authoring and rendering
│  ├─ content-studio-understand/      # frame and audio evidence
│  ├─ content-studio-voice/           # narration methods
│  ├─ content-studio-audio/           # final audio mastering
│  ├─ content-studio-music/           # music sources and mixing
│  ├─ content-studio-memes/
│  ├─ content-studio-memory/          # preferences, Kdenlive import, learning
│  ├─ content-studio-publish/
│  │  └─ scripts/{youtube.mjs, instagram.mjs}
│  └─ content-studio-archive/
│     └─ scripts/{youtube_backup.py, drive_sync.py}
│
├─ shared/                            # reusable helpers only; no operations
├─ scripts/                           # installer and compatibility CLI
└─ tests/                             # cross-skill workflow tests
```

Every operation skill should also have its own `SKILL.md`, `methods.json`, `references/`, and `tests/`. Each precheck plan step should record the chosen skill, method ID, exact script and arguments, inputs, outputs, estimate, and review criterion. A method change should invalidate the approved plan.

Existing `content-studio` and `content-studio-videoedit` commands can remain as thin compatibility entrypoints while implementations move to their owning skill folders. The installer must discover or register the new top-level skills.
