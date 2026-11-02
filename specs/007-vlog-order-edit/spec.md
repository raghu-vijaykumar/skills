# Vlog ordering and editing

**Status:** Implemented

## Contract

Camera clips from multiple devices are ordered by capture time before draft preprocessing. `_timeline.csv` is the reviewable source of order, local timestamps, device, duration, and estimates. Inserting a new camera clip updates order and numbered filenames while preserving existing timestamp decisions. A dry run previews changes. The camera timezone offset must be supplied when it cannot be inferred from metadata and existing timeline rows.

Editors can keep a time range, remove one or more ranges, or join an ordered draft or explicit clip list. Cuts are frame accurate and do not overwrite inputs. A draft join prefers approved cut files, then processed video/audio. The joined master is 1920x1080 BT.709 SDR at 30 fps, with mixed aspect ratios padded and HDR tone mapped. Dolby Vision trim/cut requires an explicit SDR export choice because frame-accurate edits cannot retain RPU.

## Acceptance

- A newly inserted clip between two old clips updates `_timeline.csv` and numbered names without collisions or changing prior estimated timestamps.
- Draft preprocessing and draft join refresh stale ordering before selecting sources.
- Trim and multi-range cut produce duration-checked video and audio; join produces a duration-checked 1080p SDR master.
- Existing `video.mp4` and any specified output file are never overwritten.
- Dolby Vision cuts cannot silently lose Dolby metadata.
