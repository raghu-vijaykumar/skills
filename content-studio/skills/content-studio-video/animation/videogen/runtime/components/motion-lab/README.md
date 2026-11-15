# Motion primitives for Core Explainer

Import from `@raghu-vijaykumar/videogen/runtime/components/motion-lab/index` in a Remotion scene. The components are pure functions of `now` in seconds, default to Core Explainer design tokens, and accept project colors; no source footage, logos, or narration is bundled.

| Component | Input | Use |
| --- | --- | --- |
| `KineticHeadline` | Timed lines of text parts (`emphasis` for a selected word, `strong` for bold) | Reveal the spoken claim; optional `selectionHandles` reproduces an editing-cursor treatment. |
| `ChapterSpine` | Ordered `{label, start}` markers | Preserve the viewer's place across rapid scene changes. |
| `LayeredStack` | Ordered `{label, detail, color}` cards plus `start` | Introduce several system layers before inspecting one in detail. |

Choose these per teaching beat; they are not a required frame template. Render the hero alone and in its narrated scene. The first private Stripe study found that CSS stack and device stand-ins are much flatter than the reference, so use authored or licensed depth assets for delivery-quality hero objects.
