# Create and animate a 2D presenter

Use a `Presenter2D` SVG rig when the presenter needs to gesture, blink, and speak on cue. Keep character art separate from narration and timing. The same profile can be cast in a portrait or landscape scene.

## Draw the character

1. For a cartoon, caricature, or other portrayal of a specific person, start with real photos of that person. Collect a neutral front view, a three-quarter view, and a characteristic expression when available. Use a side view for a speaking turn when the angle matters. Record the person's recognizable silhouette, feature spacing, hairline, brows, nose, jaw or beard, and eyewear at the presenter’s actual size. If only one photo is available, ground the visible features in that view and record which angles still need evidence.
2. Draw original vector layers. Start with a front view for the neutral pose. Give the head a consistent origin at the base of the jaw. Use the rig’s SVG coordinate system, where the head rises from the neck anchor at `(0, 0)` and the torso extends about 200 units down. Aim for a head roughly 160 units wide by 230 high, then adjust the shot scale together with room for both hands.
3. Export your face component with `PresenterFaceProps`. Bind `eyeOpen` to the lids or eyes only, `gaze` to a small pupil offset, and `mouthOpen` to the lower lip or jaw path. Keep frames for glasses, hair, and face contours independent. Use React’s `useId` for any SVG gradients, masks, or clip paths. Pass skin and clothing colors through the palette for a consistent neck, arms, and torso.
4. Store a personal profile in `~/.agents/content-studio/presenters/<id>/` with its `presenter.tsx` export and a short README on origin, reuse, and supported poses. The local library survives skill upgrades. Copy the selected profile into the consuming project so a draft can render with its exact version. The original photo is a separate design reference.

For a new silhouette or art style, pass an SVG `body` component with `PresenterBodyProps`. The rig supplies each arm’s interpolated elbow and wrist, hand shape (`rest`, `point`, `open`, or `two`), angle, and the palette. Keep the neck on the same anchor and redraw the torso and sleeves around your proportions. Shape the forearm from elbow to wrist and attach the palm at the wrist. Use different finger silhouettes for different gestures and check both the held poses and their in-betweens.

For a caricature, choose which real features to exaggerate and which relationships make the person recognizable. Build the exaggeration into the face shapes and preserve those relationships through head turns, blinks and speech. Compare the isolated neutral pose and a representative expression with the real photos at corresponding angles. Check that the likeness reads at delivery size without the name or costume carrying the recognition.

## Bind motion to a scene

- Place the exported presenter inside a composition SVG. Its `x` and `y` locate the neck. `scale` sizes the entire rig, including its gesture reach. View the full raised hand and face before locking captions and diagram safe areas.
- Author ordered scene-local cues for `rest`, `point-left`, `point-right`, `explain`, `two`, or `present`. The left and right directions refer to the screen. Start a gesture a few frames before the thing it directs attention to. Use `transitionFrames` to set the approach and let the action hold long enough to read.
- For a contact, reaction or handoff that needs its own pose, add `pose` to a cue. The rig interpolates explicit gaze and elbow and wrist targets from the pose already on screen. `gaze` is a horizontal and vertical pair around zero, with positive vertical values looking down. A custom face can read `gazeY` independently of head rotation.
- A custom body can draw interpolated `fingers` using five extension values from thumb to little finger, with 0 curled and 1 extended. Key elbow and wrist together to keep arm length believable as the position changes. Fit the shirt sleeve to the upper arm and compute the palm angle from the forearm. Use an angle offset for the wrist turn. The default body's preset silhouettes cover the original gesture set.
- Use `blinkFrames` for blink centers. Supply speech energy normalized to 0–1 at the composition rate for simple mouth movement. For precise dialogue, author phoneme-based mouth cues in the face component and drive that channel with explicit frame timing.
- Place the character in a fixed-camera isolated preview, then in the narrated scene. Inspect the gesture start, peak, settle, and first transition into the next gesture. Check blink and speech frames and confirm that hands avoid captions and that poses actually point to the intended object.

For a presenter who follows the mechanism, write each gesture's purpose next to its cue. Specify the object, active hand, gaze target, and expected held pose. A reset at a camera cut can use a zero-frame cue. Within a continuous shot, start a new cue early enough to move into place or use an explicit recovery cue. Check finger separation, wrist attachment, elbow shape and gaze during consecutive frames as well as at the hold.

Use the [photo-based actor review](../../../../review/critique/references/photo-reference.md) to score a recognizable likeness, stylized finish, and staging. Review the rendered blink, gaze, mouth shapes and gestures separately. Use an ordered photo sequence or footage to establish a characteristic expression change. Use timed capture for the person's actual speech or gesture rhythm. Keep any subject-specific motion comparison open until the evidence supports it.

For a walking or running character, block the planted foot, lift and next landing separately. Pin the planted foot in world coordinates, solve the knee to meet the foot, and move the camera independently. Carry the position through a reaction or prop release. Use a [relative object track](../../../../review/critique/references/frame-tracing.md) across visible stance frames to verify contact under a pan. Add a second scene anchor for a uniform push-in. Inspect lift and landing by eye and confirm that the tighter framing leaves room for the held prop and the reacting character.

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
