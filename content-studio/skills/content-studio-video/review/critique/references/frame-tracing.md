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

For several meaningful changes inside a beat, put `landmarks` on the same beat row. Name the same visible state or event on both sides and map its time independently. Include frames before and at or after every time.

```json
"landmarks": [
  {"id":"card-enters","reference":54.6,"candidate":54.5},
  {"id":"history-revealed","reference":56.2,"candidate":55.1}
]
```

The viewer's landmark menu jumps both lanes to the corresponding decoded picture. Each event also gets a four-frame `landmark-<id>.jpg` sheet. Check the preceding and following frames to confirm the authored event, then use the same landmarks to compare a revision. Adjust candidate times if the choreography or edit changes.

To check word-to-action sync, put `"word_anchors": [{"id":"contact","reference":1.20,"candidate":2.41}]` on the same beat row. Use a matching landmark ID and the onset of the cue word from each lane's aligned audio. An onset may fall at the start of its mapped beat. The trace records the supplied `word_onset_seconds` and signed `word_to_picture_ms` from that onset to the first decoded picture at or after the visual landmark. The landmark sheet prints the offset on its `after` frame. Positive is picture after speech. The tool measures against supplied anchors. Check the chosen word and visible event by listening and stepping the frames, and refresh both anchors after an edit. Apply the same check when comparing two art presets played to identical narration.

For results that need time to read, map the visibly legible interval with `holds` on the same beat. For example, `"holds": [{"id":"amount-readable","reference":[109.6,112.0],"candidate":[110.7,112.5]}]`. Use first and end-exclusive times within each mapped lane. The report records the annotated duration, actual decoded frames inside the interval, and first, middle and last evidence. Use the six-frame hold sheet and step the full interval in the viewer to look for obstruction, motion blur, or loss of emphasis. Confirm readability against the actual render. The annotated duration and count measure the interval and do not judge its contents.

For a small hinge, finger contact, or display edge, add one independent `details` box per lane, such as `"details": {"reference":[0.46,0.38,0.72,0.61],"candidate":[0.28,0.41,0.60,0.67]}`. Use normalized left, top, right, bottom coordinates. Each box stays fixed within its lane for the beat. Crop before the review resize so fine features survive. The detail frames use the same decoded timestamps, and paired seams, landmarks and holds get companion `detail-*.jpg` sheets. Open the full-frame sheet for scale and clearance, then check attachment and material in the corresponding detail sheet. Split a beat or widen its box if the object moves outside it.

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

To inspect foot contact or another attachment under a camera pan, track the subject and a fixed point on the same supporting surface in one lane. Add `"relative_tracks": [{"id":"stance","subject":"shoe","anchor":"floor-edge"}]` alongside the tracks in the seed file. Use the planted portion of the action. The report subtracts the simultaneous anchor position from the subject position, reports drift from the first jointly visible frame, and retains missing samples. Read normalized drift together with joint coverage and inspect both trails for identity swaps.

For a flat scene that also zooms uniformly, add `"scale_anchor":"second-floor-mark"` to the same entry and track that distinct fixed mark in the same lane. Choose anchors far enough apart to make scale changes visible while staying in frame. The report compares their spacing to the first joint frame and compensates for translation and uniform scale before calculating drift. It records the estimated scale for each joint sample. Inspect all three trails to ensure the measured change belongs to the camera. Use a shorter window or another approach for rotation, changing perspective, or missing marks across a cut.
