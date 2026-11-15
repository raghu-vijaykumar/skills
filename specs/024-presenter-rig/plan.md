# Reusable 2D presenter rig

## Outcome

Content Studio can animate an original 2D presenter from scene cues. Users can create face art from an authorized reference and reuse it across videos. Facial art and project dialogue are independent of pose timing.

## Implementation

- Export a React/SVG presenter rig using the existing scene-local easing functions. Separate arm joints, hand silhouettes, head, blink and speech inputs.
- Give scene authors a face component contract and sample cue sequence. Store personal presets in the local Content Studio library and copy the chosen preset into each consuming draft for reproducibility.
- Draw the supplied face in editable local SVG. Test a short rendered range using existing narration and scene cues. Inspect a rest frame, hand cue, blink, and open mouth at the rendered scale.
- Test pure pose interpolation and render multiple characters together. Update the scene authoring skill, verify package and installation, then commit and push the shared implementation and documentation.
