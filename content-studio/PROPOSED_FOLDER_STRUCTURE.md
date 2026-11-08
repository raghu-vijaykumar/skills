# Proposed Content Studio folder structure

Status: draft for review and editing. This describes the intended organization, not the current files.

Keep all video-specific skills and implementations under one content-studio-video/ source folder. Every category and operation folder under it is an individually usable skill with its own SKILL.md; internal scripts, references, and tests folders are supporting files. Category skills route work, and operation skills run one type of work. Put alternative ways to perform an operation in separate scripts. The lifecycle router and precheck workflow remain at the Content Studio level because they coordinate the video operations.

~~~text
content-studio/
├─ skills/
│  ├─ content-studio/                      # lifecycle router
│  ├─ content-studio-workflow/             # system precheck and approved plan
│  │  ├─ SKILL.md
│  │  ├─ scripts/
│  │  │  ├─ profile.py
│  │  │  ├─ plan.py
│  │  │  ├─ approve.py
│  │  │  └─ run.py
│  │  └─ tests/
│  │
│  └─ content-studio-video/                # video domain router
│     ├─ SKILL.md
│     ├─ planning/
│     │  ├─ SKILL.md
│     │  ├─ ideagen/                       # owned analytics, public comparisons, idea plan
│     │  └─ styles/                        # merged catalogue and style engine
│     │     ├─ SKILL.md
│     │     ├─ catalogue.ts                # one registry of built-in style contracts
│     │     ├─ themes.ts                   # separate theme identities
│     │     ├─ scripts/{list.mjs, style_engine.py, storyboard.py,
│     │     │           style_consistency.py, looks.py, style_render.py}
│     │     ├─ core-explainer/
│     │     │  ├─ SKILL.md
│     │     │  ├─ runtime/
│     │     │  └─ references/core-explainer.md
│     │     ├─ tech-dispatch/
│     │     │  ├─ SKILL.md
│     │     │  ├─ runtime/
│     │     │  └─ references/tech-dispatch.md
│     │     ├─ evidence-lab/
│     │     │  ├─ SKILL.md
│     │     │  ├─ runtime/
│     │     │  └─ references/evidence-lab.md
│     │     ├─ rapid-take/
│     │     │  ├─ SKILL.md
│     │     │  ├─ runtime/
│     │     │  └─ references/rapid-take.md
│     │     └─ hairline/
│     │        ├─ SKILL.md
│     │        ├─ runtime/
│     │        ├─ references/hairline.md
│     │        └─ upstream/                # licensed historical source
│     │
│     ├─ source/
│     │  ├─ SKILL.md
│     │  ├─ ingest/
│     │  │  └─ scripts/{order.py, dedupe.py}
│     │  ├─ preprocess/                    # coordinates approved source operations
│     │  │  ├─ SKILL.md
│     │  │  ├─ methods.json                # keep source, SDR export, DV-preserving path
│     │  │  ├─ scripts/{inspect.py, prepare_clip.py, render_sdr.py,
│     │  │  │           render_dolby_vision.py, assemble.py, verify.py}
│     │  │  ├─ references/{workflow.md, output-layout.md, hdr-dv.md}
│     │  │  └─ tests/
│     │  ├─ blur-review/
│     │  │  └─ scripts/{detect.py, apply_approved_cuts.py}
│     │  └─ stabilize/
│     │     └─ scripts/vidstab.py
│     │
│     ├─ edit/
│     │  ├─ SKILL.md
│     │  ├─ autocut/                       # experimental; explicit request only
│     │  │  └─ scripts/{heuristic_select.py, transcript_select.py,
│     │  │              annotation_select.py, render.py, review.py}
│     │  ├─ reframe/
│     │  │  └─ scripts/{subject_boxes.py, saliency.py, center.py}
│     │  ├─ clip-edit/
│     │  │  └─ scripts/{trim.py, cut.py, join.py}
│     │  ├─ color/
│     │  │  └─ scripts/{preset.py, lut.py, shot_match.py}
│     │  ├─ upscale/                       # edited picture before code-generated overlays
│     │  │  └─ scripts/{lanczos.py, real_esrgan.py, compare.py}
│     │  ├─ restoration/
│     │  │  └─ scripts/{lens.py, video_denoise.py, deflicker.py,
│     │  │              video_deblur.py, sharpen.py, refine.py}
│     │  └─ motion-graphics/
│     │
│     ├─ animation/
│     │  ├─ SKILL.md
│     │  ├─ videogen/                       # Remotion router and shared runtime
│     │  │  ├─ SKILL.md
│     │  │  ├─ scripts/cli.mjs              # compatible videogen command
│     │  │  ├─ project-setup/
│     │  │  │  ├─ SKILL.md
│     │  │  │  ├─ scripts/{init.mjs, scaffold.mjs}
│     │  │  │  └─ templates/project/
│     │  │  ├─ scene-authoring/
│     │  │  │  ├─ SKILL.md
│     │  │  │  ├─ runtime/{animation, components, remotion, three}/
│     │  │  │  └─ references/video.md
│     │  │  ├─ narration-timing/
│     │  │  │  ├─ SKILL.md
│     │  │  │  └─ scripts/{narration.mjs, verify-narration.mjs}
│     │  │  ├─ render/
│     │  │  │  ├─ SKILL.md
│     │  │  │  └─ scripts/{preview-range.mjs, delivery.mjs}
│     │  │  ├─ validation/
│     │  │  │  ├─ SKILL.md
│     │  │  │  └─ scripts/{check-*.mts, frame-probe.mjs}
│     │  │  └─ content-output/
│     │  │     ├─ SKILL.md
│     │  │     ├─ scripts/{content-check.mjs, content-render.mjs}
│     │  │     └─ references/posts.md
│     │  └─ engineering-3d/                # Blender technical cutaway skill
│     │     ├─ SKILL.md
│     │     ├─ scripts/{model_assets.py, engineering_timeline.py,
│     │     │           engineering_blender.py}
│     │     ├─ examples/illustrative-cpu-assembly.json
│     │     ├─ references/engineering-cutaway.md
│     │     └─ tests/
│     │
│     ├─ audio/                             # one home for all video audio operations
│     │  ├─ SKILL.md
│     │  ├─ source-cleanup/
│     │  │  └─ scripts/{deepfilter.py, afftdn.py, keep_source.py}
│     │  ├─ voice-cloning/
│     │  │  └─ scripts/{enroll.py, indicf5.py, verify_clone.py}
│     │  ├─ narration/
│     │  │  └─ scripts/{recorded_voice.py, cloned_voice.py,
│     │  │              assemble.py, mix_into_video.py}
│     │  ├─ music/
│     │  │  └─ scripts/{youtube_library.py, pixabay.py, mix.py}
│     │  └─ mastering/
│     │     └─ scripts/master.py
│     │
│     ├─ review/
│     │  ├─ SKILL.md
│     │  ├─ understand/                    # frame and audio evidence
│     │  ├─ quality/                       # SSIM, PSNR, VMAF
│     │  ├─ benchmark/                     # synchronized visual comparisons
│     │  └─ final-render/                  # exact delivered picture and audio review
│     ├─ memory/                           # persistent editing preferences across chats
│     │  └─ scripts/{preferences.py, review_events.py, kdenlive_import.py,
│     │              compare_edits.py, learning_candidates.py}
│     ├─ memes/                            # catalogue and approved insertions
│     └─ delivery/
│        ├─ SKILL.md
│        ├─ publish/
│        │  └─ scripts/{youtube.mjs, instagram.mjs}
│        └─ archive/
│           └─ scripts/{youtube_backup.py, drive_sync.py}
│
├─ shared/                                 # reusable helpers only; no operations
├─ scripts/                                # installer and compatibility CLI
└─ tests/                                  # cross-skill workflow tests
~~~

Every category and operation folder under content-studio-video/ has its own SKILL.md and can be invoked directly without first invoking content-studio-video/ or a category skill. Category folders are router skills. Each leaf operation folder also has methods.json, references/, scripts/, and tests/, and declares its dependencies on shared bundle code explicitly. A folder with one supported method still records that method. Shared helpers do not become skills unless they perform an independently reviewable operation.

The current content-studio-styles skill already combines the style catalogue and style engine. The proposal keeps them together in planning/styles/; it does not recreate a separate style-engine skill.

## Preprocess contents

preprocess/ is the independently callable coordinator for preparing raw camera clips for editing. It reads the approved precheck plan and invokes ingest/ for ordering and deduplication, audio/source-cleanup/ for diagnosed voice treatment, blur-review/ for candidate spans and approved cuts, and source/stabilize/ for approved stabilization. Those operation skills remain usable on their own. The coordinator records the source hash, selected method, parameters, review state, and exact outputs for each clip.

- inspect.py probes streams, orientation, frame rate, resolution, HDR/Dolby Vision metadata, audio, and available disk space without changing the source.
- prepare_clip.py applies only the approved source operations and keeps the camera original in original/. It does not interpret blur detection as permission to cut.
- render_sdr.py makes a new normalized SDR clip only after an explicit HDR tone-map decision when needed. render_dolby_vision.py uses the proof and approval route when preserving Dolby Vision RPU; if verification cannot preserve it, the source video remains available with the cleaned audio as a separate asset.
- assemble.py is optional: only an explicit request joins approved clips into <id>-preprocessed.mp4. The default handoff is a folder of individually prepared clips for manual editing. verify.py checks each exact rendered clip and its audio, including duration, orientation, color tags, DV frame/RPU alignment where applicable, and approved source ranges.

Per-clip reports, review media, and processed outputs live under .content-studio/processed-clips/<clip>/; the capture-order record stays at .content-studio/_timeline.csv. A detected blur span is review evidence until a human marks it for removal. Re-running with the same source hash and approved method should reuse verified outputs; a source or method change requires fresh analysis and review. The current implementation is mainly [preprocess.py](skills/content-studio-videoedit/scripts/preprocess.py) behind the [preprocess skill](skills/content-studio-videopreprocess/SKILL.md); these named scripts are the proposed split, not files that already exist.

## Default camera-footage workflow and paths

The default is manual editing. A folder of camera videos triggers only the approved preprocessing phase; it does not trigger AutoCut, an automatic story edit, narration, overlays, or upscale. AutoCut is an experimental alternative used only when the user explicitly requests it. An initial precheck covers the source preparation and handoff. When the user later supplies a rendered edit and asks for more work, show and approve a new or revised precheck plan naming the voice, graphics, and optional upscale methods.

| When | What happens by default | Output and stop point |
| --- | --- | --- |
| User supplies a folder of raw videos | Inspect sources and capacity; order and deduplicate; diagnose audio, blur, stabilization, and HDR/DV; apply only approved source fixes. Preserve the supplied folder. | Copy or reference raw files under `drafts/<id>/original/`; put prepared clips and reports in `drafts/<id>/.content-studio/processed-clips/` and capture order in `.content-studio/_timeline.csv`. Stop and hand off the clips. |
| User edits the prepared clips | The user chooses shots, trims, transitions, and story in their own editor. No AutoCut or automatic join runs. | User supplies `drafts/<id>/<id>-manual-edit.mp4`, or identifies an existing file; record its path and hash without replacing it. |
| User asks for a voice script on that render | Use `review/understand/` on the supplied render, sample frames and audio, add user context for uncertain facts, then write a timed, evidence-linked script. | `.content-studio/understanding/evidence.json`, `voiceover.json`, `voiceover.md`, and timing report. Stop for script and timing review. |
| User approves script and requests generated voice | Use the selected approved voice method; cloning requires a consented profile and a listening check. Assemble and mix the approved narration against the manual edit without changing its picture. | `.content-studio/voice/narration.wav`, timeline and review audio; `.content-studio/voice/with-voice.mp4` after mix review. |
| Completed edit needs higher delivery resolution | Diagnose the edited video after any requested voice mix, before overlays. Compare bounded untouched/Lanczos/AI ranges, estimate whole-video runtime, and upscale this one completed edit only when the evidence and user review support it. Skip when clean or already sufficient. | `.content-studio/upscale/` comparison and decision report, plus `.content-studio/upscale/upscaled-edit.mp4` only if approved. No per-clip upscale batch. |
| User requests motion graphics on specific scenes | Use times in the manual edit, checked against the voiced/upscaled edit, and create a cue sheet only for named scenes. Render code-generated graphics at the delivery resolution over that edit; review placement, text, motion, color, and audio. | `.content-studio/motion-graphics/cues.json`, optional ASS sidecar, review clips, and `.content-studio/motion-graphics/with-graphics.mp4` when a combined render is approved. Graphics are not upscaled. |
| Final file is ready | Review affected ranges and the entire delivered picture and audio, then prepare metadata and package for separate approval. | `drafts/<id>/<id>-final.mp4` from the verified overlaid edit, or from the voiced/upscaled edit if no graphics were requested, plus review records. Publishing remains a separate explicit request. |

The manual edit is the time reference for voice and graphics. If that render changes, its hash invalidates their timing and review evidence. The voiced edit is the input to the upscale decision when voice was requested; otherwise use the manual edit. Overlay generation uses the verified upscale output when present, or that same unscaled edit when upscale was skipped, so code-generated graphics remain sharp at delivery resolution. Upscale must preserve timing or the overlay cues need fresh review. Preserve each input and intermediate output. For Dolby Vision, prefer a sidecar or an explicitly reviewed tone-map path rather than silently losing RPU.

## Existing built-in style catalogue

The current list command reports five built-in styles. These are the current source and reference locations, before the proposed move:

| Style | Formats | Current implementation | Current references |
| --- | --- | --- | --- |
| Core Explainer | Video, carousel, post | [style registry](skills/content-studio-videogen/runtime/styles.ts), [editorial metadata](skills/content-studio-videogen/runtime/design/contentStyles.mjs), [shared design tokens](skills/content-studio-videogen/runtime/design/color.ts) | [video guidance](skills/content-studio-videogen/references/video.md), [themes and styles](skills/content-studio-videogen/references/themes.md); no dedicated Core Explainer reference |
| Tech Dispatch | Carousel, post | [design tokens](skills/content-studio-videogen/runtime/design/techDispatch.ts) | [post guidance](skills/content-studio-videogen/references/posts.md); no dedicated Tech Dispatch reference |
| Evidence Lab | Video, carousel, post | [design tokens](skills/content-studio-videogen/runtime/design/evidenceLab.ts) | [video guidance](skills/content-studio-videogen/references/video.md); no dedicated Evidence Lab reference |
| Rapid Take | Video | [design tokens](skills/content-studio-videogen/runtime/design/rapidTake.ts), [components](skills/content-studio-videogen/runtime/components/rapid-take/RapidTake.tsx) | [Rapid Take reference](skills/content-studio-videogen/references/rapid-take.md) |
| Hairline Animation | Video | [runtime](skills/content-studio-videogen/runtime/hairline.tsx), [licensed upstream source](skills/content-studio-styles/hairline-source/LICENSE) | [Hairline reference](skills/content-studio-videogen/references/hairline.md) |

The [list command](skills/content-studio-styles/scripts/list.mjs) reads the built-in IDs and formats from the [style registry](skills/content-studio-videogen/runtime/styles.ts) and descriptions from [editorial metadata](skills/content-studio-videogen/runtime/design/contentStyles.mjs). Hairline's description is supplied by the list command because it has no entry in that second file. The proposed catalogue.ts consolidates those built-in fields into one registry. The built-in themes are neutral and revise-labs; a project may enable only a subset of styles or add custom ones. Tech Dispatch currently supports carousel and post, not video.

## Animation contents

The animation/ skill routes an approved visual beat to the appropriate renderer. The styles skill chooses the treatment; an animation skill builds and renders it. Each named operation under videogen/ and engineering-3d/ remains directly callable, with its own precheck, method choice, evidence, and tests.

The current [videogen skill](skills/content-studio-videogen/SKILL.md) and [CLI](skills/content-studio-videogen/scripts/cli.mjs) provide project initialization and scaffolding, Remotion Studio preview, narration cues, scene checks, bounded evidence renders, full delivery renders, and carousel/post output. Its [runtime](skills/content-studio-videogen/runtime/project.ts) includes reusable animation, components, Remotion registration, and 3D helpers; [project templates](skills/content-studio-videogen/templates/project/videogen.config.ts) create a starting configuration. The proposed project-setup/, scene-authoring/, narration-timing/, render/, validation/, and content-output/ skills give those operations separate entrypoints. The current CLI contains some render and setup logic directly, so preview-range.mjs, delivery.mjs, and init.mjs are proposed extractions rather than existing files. Platform publishing belongs in delivery/publish/, and style-specific components and references belong with their style skills.

The current engineering cutaway implementation sits in the merged styles skill: [model_assets.py](skills/content-studio-styles/scripts/model_assets.py) imports approved GLB, glTF, or FBX meshes; [engineering_timeline.py](skills/content-studio-styles/scripts/engineering_timeline.py) applies component and camera events; [engineering_blender.py](skills/content-studio-styles/scripts/engineering_blender.py) renders the authored Blender scene. The [CPU example](skills/content-studio-styles/examples/illustrative-cpu-assembly.json) is illustrative geometry, not a faithful hardware model. The proposed engineering-3d/ skill moves these files together and gives their source-asset, timing, and render checks one reference and test area. It must not claim to infer accurate hardware geometry, arbitrary cross sections, or narration alignment from the model automatically.

## Review and iterative improvement

Review is a loop at several points, not one pass after editing:

1. Before the production plan, use review/understand/ to sample source frames and audio, diagnose specific issues, and record baseline evidence. The precheck names the proposed operation and exact method script, or records SKIP when no issue is found.
2. After the user's manual edit render, review story, scene times, framing, and sound. Review an AutoCut rough cut here only if the user explicitly requested that experimental route.
3. For each diagnosed issue, run bounded candidates through its individual operation script, including an untouched-source candidate. Use review/quality/ for applicable measurements and review/benchmark/ when a synchronized visual or audio comparison makes the choice clearer. Record parameters, source hash, rejected alternatives, side effects, and a FIX, SKIP, REVIEW, or UNSUPPORTED decision for that issue.
4. Apply approved source cleanup before the manual edit. After the user supplies the rendered edit, complete requested voice work, consider upscale on that one edited video, then render requested code-generated graphics at delivery resolution. A failed candidate can trigger one bounded alternative and another comparison; unresolved or subjective results remain REVIEW or SKIP rather than being called fixed.
5. Render the exact selected timeline and run the relevant quality checks again on affected ranges. review/final-render/ checks representative frames, transitions, audio, and the whole delivered master. The final output must meet the original acceptance criterion before the package review can finish.

Each review operation is an individually callable skill. The review router records checkpoints and evidence, while the editing operation owns its method scripts. Current refine.py already compares off, light, and medium polish proxies and offers --verify-render for final-output checks; the proposed structure separates those methods without losing that loop.

video_deblur.py in the proposed tree is a future method slot, not a current working deblur backend. The current restoration guidance calls deblurring conservative sharpening and says it cannot recover truly lost detail or missed focus. Until a real method is benchmarked and verified on delivered output, mark a deblur request REVIEW or UNSUPPORTED and preserve the source.

## Audio and voice cloning

Source cleanup diagnoses and treats audio in camera clips. Mastering checks and levels the final mix. These are different stages within the same audio/ domain, so there is no separate top-level content-studio-audio-tune/ folder beside an audio/ folder. The edit/restoration/video_denoise.py method treats picture noise, not audio noise.

Voice cloning owns consented voice enrollment, private reference samples, the local IndicF5 synthesis method, and clone quality checks. Narration owns the approved script timing and assembly of recorded or cloned speech onto the video timeline. Consent, samples, model weights, and generated audio stay outside Git; a human listens to the clone before it reaches a final mix. Additional cloning backends get their own scripts only after they are implemented and reviewed.

## Editing memory across chats

The current content-studio-memory skill stores preferences and review events in a SQLite database only when a command receives an explicit database path. The path shown in its SKILL.md is an example, not an initialized default. AutoCut loads that database only with --memory-db; other editing operations rely mainly on instructions to retrieve preferences. Opening a new chat does not load this project database.

The proposed memory skill uses one persistent database outside Git, with a user-configured path and a Windows default of %LOCALAPPDATA%/ContentStudio/editing-memory.sqlite. All video skills resolve that same path, including when invoked individually from a new chat. At the start of every editing task, the precheck retrieves global, category, and project preferences and displays the applicable values and their sources in the editable plan. An individual skill performs the same retrieval through the shared memory interface before it proposes an edit. If the database is absent, the plan says that no saved editing preferences were found; it must not silently claim to remember earlier edits.

After explicit human review, save the decision and its project, operation, source evidence, and reason to the database. Promote a preference for future edits only after the user confirms it. Keep observational Kdenlive comparisons and learning candidates separate from confirmed preferences. An editing task in another chat reads the confirmed preferences from the same database; chat text alone is not the storage mechanism.

## Precheck and compatibility

Each precheck plan step records the operation folder, selected method ID, exact script and arguments, inputs, outputs, time estimate, fallback, and review criterion. The runner checks that the command matches the approved method. Changing the method or arguments invalidates plan approval.

The current installer exposes only direct child skills. It must recursively discover and validate every nested SKILL.md in content-studio-video/, then link each skill directly into the installed skills directory under a unique skill name. A nested operation's entrypoint and bundle dependencies must work when that skill is invoked alone. Preserve existing public skill names and CLI commands as compatibility entrypoints; their implementations move into the video folder and the old entrypoints remain thin dispatchers. Direct specialist use still follows the mandatory precheck.
