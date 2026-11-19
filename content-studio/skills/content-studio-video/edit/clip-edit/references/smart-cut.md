# Guarded H.264 cut comparison

`smart-cut-candidate` is an optional comparison for an explicitly requested cut
of one H.264 source. Complete the mandatory workflow precheck and name this
method, source, frame-aligned removal ranges, candidate output, report, time
estimate, and `accurate-cut` fallback in the approved plan. The raw camera
folder still goes to manual editing by default.

From this skill folder, after plan approval:

```powershell
python scripts/smart_cut.py --input <approved-sdr-h264.mp4> --remove 00:02.333333-00:04.666667 --out <draft>/.content-studio/tmp/smart-cut-candidate.mp4 --report <draft>/.content-studio/analysis/smart-cut.json
```

The method accepts only one 8-bit yuv420p H.264 video stream, zero or one AAC
audio stream, explicitly tagged SDR transfer, constant decoded frame timing,
zero display rotation, frame-aligned cut points, and at least one complete GOP
to copy. HDR, Dolby Vision, VFR, other codecs, unknown transfer, multiple
streams, and picture effects stay on the accurate route. It encodes only
boundary picture groups, copies complete interior GOPs, and encodes the
retained source audio once. This comparison needs local space for temporary
video segments; it does not change originals.

`PASS_CANDIDATE` means the report has the source SHA-256, planned frame ranges,
packet hashes for copied interior frames, count and sampled luminance error for
every decoded frame, and start/duration plus correlation of audio windows at
the joins. MP4 may rewrite SPS/PPS in the first packet of a copied GOP; the
report counts those separately. It also records the accurate-route baseline
(all retained picture frames reencoded), the copied/encoded frame split, and
candidate hash. If less than half the picture can be copied, mark `SKIP` and
use the accurate route. `REVIEW` may preserve a comparison file but it cannot
be selected as a delivery. `UNSUPPORTED` records a failed guard.

After a technical pass, review every boundary visually and by listening.
Record `FIX`, `REVIEW`, or `SKIP` with the issue, baseline, chosen candidate,
rejected alternatives, and link to the report. If any boundary fails, adjust
only that proposed cut and rerun the bounded comparison, or select
`accurate-cut`. When the selected edit becomes a package candidate, run exact
master review on its hash; a pass here does not grant package approval.

For an unsupported or uncertain comparison, use the existing accurate cut:

```powershell
python scripts/content.py edit cut --input <approved-source.mp4> --remove <start-end> --out <new-edit.mp4>
```

If a later picture operation would reencode the candidate, its packet-copy
benefit disappears. Use the approved versioned timeline and accurate final
render for that combination. Do not describe this candidate as the unified
timeline renderer.
