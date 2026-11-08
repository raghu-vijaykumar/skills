# Content Studio video structure and workflow

This is the editable map for the migrated bundle. Every directory below with `SKILL.md` is independently discoverable. Old `content-studio-*` names remain thin compatibility entrypoints. Source implementations, references, and tests live under [`content-studio-video/`](skills/content-studio-video/). `methods.json` distinguishes working scripts from unsupported requests.

```text
content-studio/skills/
  content-studio/                    lifecycle router
  content-studio-workflow/           mandatory precheck and checklist
  content-studio-video/
    SKILL.md                         stage router
    shared/dispatch.py              method-to-backend dispatch
    planning/
      ideagen/                       research and draft planning
      styles/                        merged catalogue and style engine
        core-explainer/              style guidance
        tech-dispatch/               carousel/post treatment
        evidence-lab/                evidence-led treatment
        rapid-take/references/       satirical video treatment
        hairline/references/         line-art; upstream/ attribution
    source/
      ingest/                        capture order
      blur-review/                   approved blur-range cuts
      stabilize/                     stabilizer variants
      preprocess/                    individual-clip preparation
    edit/
      clip-edit/                     shared edit backend and manual-edit tools
      autocut/                       experimental; explicit request only
      reframe/                       subjects, saliency, center
      color/                         correction and range presets
      restoration/                   denoise, deflicker, lens, sharpen
      reflection/                    detect, conservative glare/veil fix, preview, benchmark, DSRNet AI review pass
      upscale/                       compare, Lanczos, Real-ESRGAN, PyTorch
      transitions/                   point effects and explicit clip joins
      motion-graphics/               scene-cued overlays and transitions
    animation/
      videogen/                      Remotion runtime, CLI, templates
        project-setup/              init and scaffold
        scene-authoring/             authoring and preview
        narration-timing/           narration cues
        render/                     bounded preview and delivery
        validation/                 check and probe
        content-output/             carousel and post
      engineering-3d/               model import, timeline, Blender render
    audio/
      source-cleanup/               camera-audio methods
      voice-cloning/                consented sample and IndicF5
      narration/                    script timing and video mix
      mastering/                    final mix diagnosis and loudness
      music/                        licensed selection
    review/
      understand/                   frame and sound evidence
      quality/                      objective measurements
      benchmark/                    synchronized comparisons
      final-render/                 exact-master human review
    memory/                          private SQLite decisions
    memes/                           optional scene punctuation
    delivery/
      publish/                      explicit request only
      archive/                      independent public-upload backup
```

## Default camera-footage path

| When | Action | Output and stop |
| --- | --- | --- |
| Raw video folder arrives | Precheck; inspect originals and machine; determine order and duplicates; diagnose blur, sound, motion, and HDR/DV; compare only justified cleanup; prepare and verify **individual clips**. | `.content-studio/_timeline.csv` and `.content-studio/processed-clips/` for the user's manual edit. No automatic join, rough cut, voice, or upscale. |
| User supplies a manually rendered edit | Start a new edited-render precheck. Inspect the exact video and its scene times. | A method-specific plan for only requested work. |
| User requests narration | Generate an evidence-linked timed script from the render; obtain script review; record or synthesize approved voice; listen; mix onto the render without changing its picture stream. | A separate voiced master and mix report. Cloning needs consent. |
| Completed edit needs higher resolution | Compare untouched, Lanczos, and applicable AI samples on that **one edited video**; gate detail, noise, flicker, timing, color, and HDR/DV; render only an approved method. | One upscaled edit or a documented SKIP/REVIEW. |
| User requests overlays for named scenes | Cue and render code-generated graphics **after any upscale**, at delivery resolution. | Final candidate with reviewed cues and transitions. |
| Final candidate exists | Review exact picture and audio, metadata, thumbnail, and rights; separately authorize publication. | Approved master/package. Archive runs independently. |

AutoCut is experimental and requires the user's explicit request and its own approved plan. It does not replace the raw-folder handoff. A blur flag is review evidence, never automatic permission to remove footage. Camera originals and project edits stay intact.

## Precheck and iterative review

Before any production edit, including a direct leaf skill call, [`content-studio-workflow`](skills/content-studio-workflow/SKILL.md) records source, system profile, bounded benchmarks, selected operation and method ID, **exact script command and arguments**, inputs, outputs, time estimate, fallback, and acceptance/review criterion. The user reviews the editable plan; the approval hash changes with any revision. The workflow runner rejects a command that differs from its approved plan step. Direct script calls follow the same precheck gate through their skill instructions.

For each issue, record baseline evidence, compare bounded candidates with leaving the source alone, select `SKIP`, `FIX`, `REVIEW`, or `UNSUPPORTED`, and verify the **exact delivered output**. Technical metrics do not settle subjective color, cleanup, or story choices. `review/understand/` supplies evidence before the plan and at the manual-render handoff; `review/quality/` and `review/benchmark/` compare candidates; `review/final-render/` checks the exact master. `edit/restoration/` owns picture denoise/sharpen/deflicker; `edit/reflection/` owns reflection diagnosis, conservative minor glare/veil cleanup, bounded previews, licensed-backend benchmarks, and an optional DSRNet `ai` review pass. `edit/transitions/` separates time-preserving point effects from clip joins that change duration. `audio/source-cleanup/` owns camera-audio noise reduction. A faithful deblur backend remains unsupported, and content-rich reflection removal stays REVIEW/UNSUPPORTED; the DSRNet pass attenuates a predicted layer and never reconstructs occluded content.

## Styles and animation

The merged [`styles`](skills/content-studio-video/planning/styles/SKILL.md) skill chooses treatment and lists project-enabled styles. Its current registry and shared render components remain in the [`videogen runtime`](skills/content-studio-video/animation/videogen/runtime/styles.ts); dedicated style skills hold the references. Core Explainer, Evidence Lab, and Rapid Take support video; Tech Dispatch supports carousel and post; Hairline is video-only. See the [Rapid Take reference](skills/content-studio-video/planning/styles/rapid-take/references/rapid-take.md), [Hairline reference](skills/content-studio-video/planning/styles/hairline/references/hairline.md), and [runtime design tokens](skills/content-studio-video/animation/videogen/runtime/design/). Each style skill can be invoked directly, then uses `animation/videogen/` to author and render. Its child skills separate setup, scene work, cue timing, bounded rendering, validation, and post/carousel export. `engineering-3d/` holds model import, authored Blender timeline events, an illustrative CPU example, and render scripts; it does not infer accurate hardware internals or automatic speech alignment.

## Audio and voice cloning

There is one `audio/` domain. Camera-audio cleanup runs, when justified, before the user's manual edit; mastering checks the final mix. Voice cloning owns consent, private reference samples, IndicF5 synthesis, and listening review. Narration owns script timing and mixing approved speech onto a supplied render. Samples, weights, generated audio, and consent evidence stay outside Git. Picture denoise belongs to `edit/restoration/`, not audio. The old `content-studio-audio` name is a compatibility route; `content-studio-audio-tune` is retired.

## Editing memory across chats

[`memory`](skills/content-studio-video/memory/SKILL.md) uses a private database at `%LOCALAPPDATA%/ContentStudio/editing-memory.sqlite` on Windows, or the XDG state directory elsewhere. `CONTENT_STUDIO_MEMORY_DB` overrides it. Precheck retrieves confirmed global, category, and project preferences into each new plan; direct skills retrieve from that same path. If no database exists, the plan says so. Only explicit user-confirmed preferences are reused. Review events and Kdenlive observations are stored separately and never promoted automatically. Memory is not an approval or a claim that an individual chat is remembered.

## Migration status

The nested skills, recursive installer, compatibility entrypoints, method scripts, precheck routes, and narration mix are implemented here. The large clip-edit engine and shared Remotion style runtime remain shared backends behind separate operation entrypoints; extracting their internals further is optional cleanup. Unsupported methods are declared in `methods.json`, rather than exposed as working scripts. Test and release status is recorded in the feature spec and Git history.
