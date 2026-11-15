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

## Review record

1. Record the two exact files, format, intent, mapped duration, known omissions, and any audit limits. Label a preview as a preview.
2. For each important beat, describe what the source actually shows followed by what the candidate does. Note cuts, onset, impact and settle, camera and object tracks, masking and depth, readable hold, presenter pose and speech, and audible accents. Record the smallest relevant time range on each side.
3. Prioritize missing or misleading actions first, then continuity, staging, and speech sync, then surface polish. Keep useful differences if they clarify the mechanism. Use `missing`, `partial`, `matched`, or `not reviewed` per finding. A playable MP4 and a high image similarity score cannot establish a creative match.
4. Give each top finding a specific next edit and retest. For example, “keep the lost reply on screen at the point of failure, then relaunch the matching request from the phone on the retry cue; inspect the start, failure and relaunch with the camera fixed.” Require another review of the narrated cut after proof at the object level.
