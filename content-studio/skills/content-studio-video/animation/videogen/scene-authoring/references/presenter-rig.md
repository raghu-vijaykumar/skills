# Create and animate a 2D presenter

Use a `Presenter2D` SVG rig when the presenter needs to gesture, blink, and speak on cue. Keep character art separate from narration and timing. The same profile can be cast in a portrait or landscape scene.

## Draw the character

1. Choose a reference the project can use. Record the likeness cues that matter at the presenter’s actual size, such as hair shape, facial proportions, brows, beard, and eyewear.
2. Draw original vector layers. Start with a front view for the neutral pose. Give the head a consistent origin at the base of the jaw. Use the rig’s SVG coordinate system, where the head rises from the neck anchor at `(0, 0)` and the torso extends about 200 units down. Aim for a head roughly 160 units wide by 230 high, then adjust the shot scale together with room for both hands.
3. Export your face component with `PresenterFaceProps`. Bind `eyeOpen` to the lids or eyes only, `gaze` to a small pupil offset, and `mouthOpen` to the lower lip or jaw path. Keep frames for glasses, hair, and face contours independent. Use React’s `useId` for any SVG gradients, masks, or clip paths. Pass skin and clothing colors through the palette for a consistent neck, arms, and torso.
4. Store a personal profile in `~/.agents/content-studio/presenters/<id>/` with its `presenter.tsx` export and a short README on origin, reuse, and supported poses. The local library survives skill upgrades. Copy the selected profile into the consuming project so a draft can render with its exact version. The original photo is a separate design reference.

For a new silhouette or art style, pass an SVG `body` component with `PresenterBodyProps`. The rig supplies each arm’s interpolated elbow and wrist, hand shape (`rest`, `point`, `open`, or `two`), angle, and the palette. Keep the neck on the same anchor and redraw the torso and sleeves around your proportions. Shape the forearm from elbow to wrist and attach the palm at the wrist. Use different finger silhouettes for different gestures and check both the held poses and their in-betweens.

## Bind motion to a scene

- Place the exported presenter inside a composition SVG. Its `x` and `y` locate the neck. `scale` sizes the entire rig, including its gesture reach. View the full raised hand and face before locking captions and diagram safe areas.
- Author ordered scene-local cues for `rest`, `point-left`, `point-right`, `explain`, `two`, or `present`. The left and right directions refer to the screen. Start a gesture a few frames before the thing it directs attention to. Use `transitionFrames` to set the approach and let the action hold long enough to read.
- Use `blinkFrames` for blink centers. Supply speech energy normalized to 0–1 at the composition rate for simple mouth movement. For precise dialogue, author phoneme-based mouth cues in the face component and drive that channel with explicit frame timing.
- Place the character in a fixed-camera isolated preview, then in the narrated scene. Inspect the gesture start, peak, settle, and first transition into the next gesture. Check blink and speech frames and confirm that hands avoid captions and that poses actually point to the intended object.

## Wire a profile into Core Explainer

Add a `renderPresenter` callback to `ExplainerFilm` and return an SVG overlay at composition size. The hook receives the scene and its local frame. Beats with `presenter.pose: 'none'` skip the presenter. Existing presenter-image drafts can continue using their current props.

```tsx
import type {PresenterCue} from '@raghu-vijaykumar/videogen/runtime/presenter2d';
import {ExplainerFilm} from '@raghu-vijaykumar/videogen/runtime/motionExplainer';
import {PortraitPresenter} from './presenter';

const cues: PresenterCue[] = [
  {frame: 5, gesture: 'point-left', transitionFrames: 9},
  {frame: 42, gesture: 'two', transitionFrames: 8},
  {frame: 80, gesture: 'present', transitionFrames: 10},
];

export const Video = () => (
  <ExplainerFilm plan={plan} renderPresenter={(scene, frame) => (
    <svg viewBox={`0 0 ${plan.width} ${plan.height}`} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      <PortraitPresenter frame={frame} x={plan.width * 0.8} y={plan.height - 200}
        cues={scene.id === 'retry' ? cues : []} blinkFrames={[30, 102]}
        speech={energy[scene.startFrame + frame] ?? 0}/>
    </svg>
  )}/>
);
```

In a custom SVG scene, mount the profile directly as a child of that SVG. Keep the cue and audio envelope data in the scene so the same character can play different roles.
