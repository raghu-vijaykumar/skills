# Video capability matrices

Every leaf video skill, plus the [Styles](planning/styles/README.md) router, has a
capability matrix that states what the skill claims, how it reaches the delivery
timeline, and which committed evidence supports the claim. The same tables are
validated by `npm run check:capabilities`.

- **Template:** [CAPABILITY-MATRIX-TEMPLATE.md](CAPABILITY-MATRIX-TEMPLATE.md)
- **Checker:** [check-capability-matrices.mjs](../../scripts/check-capability-matrices.mjs)
- **Evidence review:** [CAPABILITY-EVIDENCE-AUDIT.md](CAPABILITY-EVIDENCE-AUDIT.md)
- **Current coverage:** 42 matrices, 111 declared methods, and 6 explicitly
  unsupported methods.

`Supported` means the manifest provides a runnable script. `Unsupported` means the
manifest declares no script and the matrix makes no capability claim.
`Yes` in the delivery-timeline column means the single-render timeline consumes an
equivalent operation; `Specialist only` means a bounded preview carries the
approved result forward. Gallery examples are illustrative, not masters.

## Animation

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Engineering 3D | [README](animation/engineering-3d/README.md) | 1 |
| Content output | [README](animation/videogen/content-output/README.md) | 2 |
| Narration timing | [README](animation/videogen/narration-timing/README.md) | 2 |
| Project setup | [README](animation/videogen/project-setup/README.md) | 2 |
| Render | [README](animation/videogen/render/README.md) | 2 |
| Scene authoring | [README](animation/videogen/scene-authoring/README.md) | documented operation |
| Validation | [README](animation/videogen/validation/README.md) | 1 |

## Audio

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Mastering | [README](audio/mastering/README.md) | 1 |
| Music | [README](audio/music/README.md) | 1 |
| Narration placement | [README](audio/narration/README.md) | 1 |
| Source cleanup | [README](audio/source-cleanup/README.md) | 3 |
| Voice cloning | [README](audio/voice-cloning/README.md) | 1 |

## Delivery

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Archive | [README](delivery/archive/README.md) | documented operations |
| Publish | [README](delivery/publish/README.md) | documented operations |

## Edit

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| AutoCut | [README](edit/autocut/README.md) | 1 |
| Clip editing | [README](edit/clip-edit/README.md) | documented operations |
| Color | [README](edit/color/README.md) | 3 |
| Motion graphics | [README](edit/motion-graphics/README.md) | 4 |
| Reflection | [README](edit/reflection/README.md) | 6 |
| Reframe | [README](edit/reframe/README.md) | 3 |
| Restoration | [README](edit/restoration/README.md) | 9 |
| Transitions | [README](edit/transitions/README.md) | 2 and 29 named transitions |
| Upscale | [README](edit/upscale/README.md) | 4 |

## Memes and memory

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Memes | [README](memes/README.md) | documented operations |
| Editing memory | [README](memory/README.md) | documented operations |

## Planning

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Ideagen | [README](planning/ideagen/README.md) | 1 |
| Styles router | [README](planning/styles/README.md) | 3 |
| Core Explainer | [README](planning/styles/core-explainer/README.md) | documented operation |
| Evidence Lab | [README](planning/styles/evidence-lab/README.md) | documented operation |
| Hairline Animation | [README](planning/styles/hairline/README.md) | documented operation |
| Rapid Take | [README](planning/styles/rapid-take/README.md) | documented operation |
| Tech Dispatch | [README](planning/styles/tech-dispatch/README.md) | documented operation |

## Review

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Benchmark | [README](review/benchmark/README.md) | 1 |
| Final render verification | [README](review/final-render/README.md) | documented workflow |
| Quality | [README](review/quality/README.md) | 1 |
| Understand | [README](review/understand/README.md) | 2 |

## Source

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Blur review | [README](source/blur-review/README.md) | 1 |
| Ingest | [README](source/ingest/README.md) | 1 |
| Preprocess | [README](source/preprocess/README.md) | 1 |
| Stabilize | [README](source/stabilize/README.md) | 1 |

## Timeline

| Skill | Matrix | Declared methods |
| --- | --- | --- |
| Delivery timeline | [README](timeline/README.md) | 48 |

## Evidence policy

Gallery inputs include synthetic cards, tones, text-to-speech, and bounded
excerpts from already published videos. Each evidence page names the source
and rebuild route. Examples are method-specific where a visual or audio
change is meaningful. Failed and review-only samples are labelled. This
gallery does not add private draft footage, new private voice recordings,
credentials, licensed music, model weights, or delivery masters. The repository
already tracks separately consented bundled voice profiles.
