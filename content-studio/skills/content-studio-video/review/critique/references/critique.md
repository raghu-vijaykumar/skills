# Map and report guide

Use seconds from the start of each local file. Ranges are half-open and at most 15 seconds. Split a long sequence at meaningful events rather than mapping an entire chapter to a highlight. IDs must be unique lowercase names with letters, digits, and hyphens. A null candidate documents a confirmed omission. Unlisted intervals appear in the coverage report as uncovered, even when the reviewer has not determined why.

```json
{
  "beats": [
    {"id": "request", "reference": [33, 36.9], "candidate": [3, 6.9]},
    {"id": "network-overview", "reference": [3, 7], "candidate": null}
  ]
}
```

The GIF aligns range starts at 12 fps without changing speed. A short side goes black after its range ends. Stills sample matching **relative positions** inside each range and label each time separately. Use new subranges anchored to action onset or impact when you need to measure timing drift. These aids are for viewing, not measuring dropped frames. Seek in the original files for frame-accurate readings and audio. File metadata and coverage are in `evidence.json`.

## Review a complete reconstruction

1. Map the whole piece by equivalent teaching beats. Use optional `--cut-threshold 0.24` to store a full-length `cut_survey` with timestamps and scores on each side. Check flagged times against the pictures. Flashes, zooms, and abrupt overlays may trigger the scan. Keep inspecting for smaller movements and dissolves that may score below the threshold.
2. Within a chapter, log one row per meaningful action. Record its actor, source in and out, candidate in and out, and visible result. A chapter can cover the same idea while omitting a transfer, intermediate state, or pose. Prioritize omissions that break the causal story.
3. Step through the dense actions and seams at native frame cadence. For an insert promoted from a short proof, check the frame before and after both boundaries in the full cut. Confirm where the actor starts, where it ends, whether its identity survives the handoff, and whether the timing still reads with the full narration and mix. Count mapped duration, inspected intervals, and verified actions separately.

## Review record

1. Record the two exact files, format, intent, mapped duration, known omissions, and any audit limits. Label a preview as a preview.
2. For each important beat, describe what the source actually shows followed by what the candidate does. Note cuts, onset, impact and settle, camera and object tracks, masking and depth, readable hold, presenter pose and speech, and audible accents. Record the smallest relevant time range on each side.
3. Prioritize missing or misleading actions first, then continuity, staging, and speech sync, then surface polish. Keep useful differences if they clarify the mechanism. Use `missing`, `partial`, `matched`, or `not reviewed` per finding. A playable MP4 and a high image similarity score cannot establish a creative match.
4. Give each top finding a specific next edit and retest. For example, “keep the lost reply on screen at the point of failure, then relaunch the matching request from the phone on the retry cue; inspect the start, failure and relaunch with the camera fixed.” Require another review of the narrated cut after proof at the object level.
