# Word choreography and art presets

Keep one frame-indexed scene plan for any number of visual presets. Rapid Take defines editorial pacing and cue density. Use anime, pixel art, or another art preset to paint that same scene. Core Explainer can use the same rig and asset workflow, with fewer actions and longer inspection holds.

1. Ground the people and objects in [real-world photos and evidence](../../../../review/critique/references/photo-reference.md). Record source views, moving parts and functional pivots. Draw original layers. For specific people, preserve identifying features and use [the presenter rig](presenter-rig.md) for wrist, eye, head and speech targets.
2. Align the final narration first. Give each Rapid Take word an actor, action and `cueKind`. Use the next step of an active reveal or reaction for short connecting words. Give each pose a reason to change and leave room for the eye to read the result. Author captions on the same frame clock.
3. Author a stable set of actor IDs and channels. Keep logical state, direction, range and contact separate from rendered coordinates. For example, `travel` is a normalized key press, while each drawing maps that progress to its own cap height and switch pivot. Assign an action to the word onset. Use independent channels for parts that move together or keep moving through the next cue.
4. Bind each art preset to all actor IDs. Each adapter draws the sampled state with the selected palette, shapes, surfaces and articulation. Anime and pixel art can use different geometry and fits while preserving the same contact and visible result. Keep the desired event timing and gesture targets in the shared plan. Use purpose-built geometry for small hands or contact points that disappear in a coarser look.
5. Render an isolated asset and a narrated clip. Check each onset, land and hold and confirm they read at speed and at native size. Run the [word cue audit](../../../../review/critique/references/reconstruction.md#inspect-the-word-clock) and [score the actors](../../../../review/critique/references/object-scoring.md). Rework the specific failing part and rerender the exact affected spans. Check caption clearance, the one focal action, and character emotion in every new look.

## Runtime

Compile at project load or memoize for a scene. Use one clock for words, art and audio. All frames are absolute within the clock supplied to the compiler. At a scene cut, use the same timeline clock or subtract the shot's start from every cue and sample with the scene-local frame. Use actor definitions in back-to-front paint order. A channel updated by the next word starts at the sampled position already visible. Unaddressed channels continue and finished channels hold. A numeric target changes immediately. A target with `frames` reaches `to` after that many frames, with linear or smooth easing.

```tsx
import {
  compileWordChoreography, WordMotionCast, WordMotionCaption,
  type WordMotionCue, type WordArtPreset,
} from '@raghu-vijaykumar/videogen/runtime/components/motion-lab/index';

const words: WordMotionCue[] = [
  {startFrame: 12, endFrame: 18, text: 'Press.', line: 0, actor: 'key', action: 'down'},
  {startFrame: 28, endFrame: 36, text: 'Release.', line: 0, actor: 'key', action: 'up'},
];
const choreography = compileWordChoreography(words, {
  key: {initial: {travel: 0}, actions: {
    down: {travel: {to: 1, frames: 5}},
    up: {travel: {to: 0, frames: 6, ease: 'smooth'}},
  }},
});

function Scene({frame, art}: {frame: number; art: WordArtPreset}) {
  return <>
    <svg width="1920" height="1080">
      <WordMotionCast choreography={choreography} art={art} frame={frame}/>
    </svg>
    <WordMotionCaption cues={words} frame={frame}/>
  </>;
}
```

An art component receives `channels` and `frame`. Bind the existing `Presenter2D` rig through shared pose or gesture data using the same word onsets. Swap its `face` and `body` drawings for a new look. Keep blinks and speech motion tied to the same aligned audio. Clamp the iris travel to each drawing's eye opening and inspect the most extreme gaze and the held reaction. Use the runtime with an authored cue plan, prepared art and a render composition.

## Long-form continuation

Once a narrated sample passes, extend the same plan by chapter. Store the selected audio, actor inventory, cues, action definitions, preset and exact review evidence with the draft. Re-align after a rewrite, recheck the changed spans in context and verify the assembled seams. Rerender a failing region and compare its exact frames and audio. Record the scorecard and remaining gaps before calling a master ready. When swapping only visual art, keep the cue signature and narration stable and verify every adapter's contact and timing in the render.
