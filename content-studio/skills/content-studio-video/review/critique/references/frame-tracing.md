# Frame tracing and object tracks

Use the paired GIF to choose one continuous beat of up to 15 seconds. Use independent time windows for the two edits. Decode every displayed frame without forcing a common frame rate:

```text
python <skill>/scripts/frame_trace.py --reference source.mp4 --candidate draft.mp4 --map beats.json --beat retry --out trace --region caption:0,0.11,1,0.27 --region mechanism:0,0.32,1,0.73 --region presenter:0.18,0.75,0.82,1
```

Open `trace/frames.html` in a browser to step each lane independently or play it at quarter speed. The 30-frame sheets enumerate consecutive pictures. When a boundary lands between frames, the trace retains the actual presentation timestamps inside the half-open range. The CSV records the picture timestamp and the percentage of luma pixels differing by at least 16 of 255 from the previous decoded image, for the full picture and each named region. This includes cuts, camera motion, fades and lighting. Treat it as an inspection cue.

For each major actor, use the sequence to log its first clear appearance, movement, interactions, final state and exit. Give a brief handoff or a one-frame jump its own row. Align by a named event such as button press or first saved result. Equal offsets from the start of a beat may correspond to different actions.

To compare a specific cut or handoff, add a seam to the same beat map. Include real frames on both sides of each anchor. The two timecodes can differ when the edits cut or change state at different moments.

```json
{"beats":[{"id":"handoff","reference":[73.2,74.2],"candidate":[74.0,74.8],"seam":{"reference":73.7,"candidate":74.4}}]}
```

The trace makes a four-frame seam sheet and records the actual decoded timestamps before and at or after the anchors. The viewer opens one frame before the seam in each lane. Use the adjacent pictures and the full sequence to verify the actor's silhouette, attachment, identifier, and state on both sides. The scorecard records the reviewer’s result.

## Track a visible actor and reuse its movement

Run `python <skill>/scripts/track_objects.py --trace trace --seeds seeds.json --out tracks` with NumPy installed. Choose a tight textured box with the frame viewer. Box units are pixels of the extracted image. `first` and `last` are inclusive, zero-based indices within this trace.

```json
{
  "tracks": [
    {"id":"reference-card", "lane":"reference", "first":12, "last":48,
     "box":[38,190,130,28], "radius":18, "threshold":0.8,
     "retarget":{"start_frame":15, "fps":30, "width":1080, "height":1920}},
    {"id":"candidate-card", "lane":"candidate", "first":15, "last":54,
     "box":[44,208,115,26], "radius":18}
  ]
}
```

Track each cut on its own. The tool matches the seed texture inside a local search window and records correlation score, normalized screen center, and displacement. The overlay draws the path on the seed frame. Inspect the tracked object against the actual frames. Similar neighboring objects can match the same seed. Label camera-relative or screen-space motion accurately. A camera push, large rotation, occlusion, transformation, or cut needs a verified new seed or a separately authored bridge.

The optional retarget settings convert the accepted displacement to pixel offsets on the target canvas and map time to scene-local frame keys. Set `time_scale` when the action has an intentionally different duration. Apply a contiguous `motion_key_segments` entry to an original actor with `MotionObject`, positioned at the target scene's initial anchor. Segments stop at loss. Use separate tracks or author the intervening action explicitly. Render the regenerated shot and track it again to check timing, displacement, and the viewer-visible result.
