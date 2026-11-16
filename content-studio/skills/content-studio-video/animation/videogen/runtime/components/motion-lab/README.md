# Motion primitives for Core Explainer

Import from `@raghu-vijaykumar/videogen/runtime/components/motion-lab/index` in a Remotion scene. The components are pure functions of `now` in seconds, default to Core Explainer design tokens, and accept project colors; no source footage, logos, or narration is bundled.

| Component | Input | Use |
| --- | --- | --- |
| `KineticHeadline` | Timed lines of text parts (`emphasis` for a selected word, `strong` for bold) | Reveal the spoken claim; optional `selectionHandles` reproduces an editing-cursor treatment. |
| `ChapterSpine` | Ordered `{label, start}` markers | Preserve the viewer's place across rapid scene changes. |
| `LayeredStack` | Ordered `{label, detail, color}` cards plus `start` | Introduce several system layers before inspecting one in detail. |
| `MotionObject` | Scene-local frame, ordered `MotionKey[]`, and SVG children | Move, rotate, scale, or reveal each original object independently. Keys inherit previous values. |
| `RoutedPacket` | Scene-local frame, start and arrival frames, endpoints, and optional stop fraction | Show a request, reply, or event traveling along a visible route. Stop the packet partway to make a failure observable. |
| `WordMotionCaption` and `sampleWordMotion` | Ordered word cues and the frame on the narration clock | Highlight every timed spoken word and get the same cue for actor choreography. Author the actor and action separately. |
| `compileWordChoreography` and `WordMotionCast` | Ordered word cues, named actor actions and an art preset keyed by actor | Sample independent rig channels at any frame and render them through interchangeable artwork. See [word choreography and art presets](../../../scene-authoring/references/word-choreography.md). |

Choose these per teaching beat; they are not a required frame template. Render the hero alone and in its narrated scene. The first private Stripe study found that CSS stack and device stand-ins are much flatter than the reference, so use authored or licensed depth assets for delivery-quality hero objects.

## Reconstruct motion from a reference

1. Sample cuts and fast actions at 5–10 frames per second and step through ambiguous frames at the reference rate. For each subshot, record source in/out frames, actors, start and end states, entrance, handoff or collision, camera change, caption cue, gesture, and sound cue. A chapter may contain several subshots.
2. Rebuild each actor from original geometry, a rig, or independently movable artwork. Draw an exploded stack as separate surfaces and side faces. Give a request, its response, and a failure each their own track. Keep a caption or speaker gesture anchored to a spoken phrase. Preserve original asset provenance.
3. Preview important actions at a fixed camera. The viewer should see what moves, where it goes, what it touches, and the result that stays after it settles. In long-form use the same actions across teaching beats, with pauses for dense diagrams and code.
4. Render the narrated shot at delivery size through the existing Remotion route. Compare equivalent actions using separate time ranges for each cut with [video critique](../../../../../review/critique/SKILL.md). Inspect anticipation, impact, and hold, including the final state the viewer needs to see. When the same item crosses screens, preserve its visual identity through the transition. Camera-only pans, label highlights, and still-image parallax are supporting moves.

```tsx
<svg viewBox="0 0 500 240">
  <MotionObject frame={localFrame} keys={[
    {frame: 0, x: 220, y: 120},
    {frame: 18, y: 65},
    {frame: 41, opacity: 0.5, ease: 'hold'},
  ]}>
    <rect x={-40} y={-16} width={80} height={32} rx={4} />
  </MotionObject>
  <RoutedPacket frame={localFrame} from={[80, 180]} to={[400, 180]}
    start={20} end={38} stop={0.6} color="#6544de" />
</svg>
```
