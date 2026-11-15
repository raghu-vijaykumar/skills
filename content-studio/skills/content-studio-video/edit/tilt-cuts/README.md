# Tilt cuts capability matrix

This skill shortlists sustained slanted scenes, previews picture and audio joins, and translates human-approved frame cuts into a native delivery timeline. A straight-edge angle is a review aid, not a calibrated camera-roll measurement.

## Capability matrix

| Capability | Status | Input → output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `scan` | Supported | SDR CFR video → source-linked, unapproved candidates and samples | No | [Synthetic scan test](tests/test_tilt.py) | Perspective, slanted objects, deliberate angles can trigger; 90-degree turns can be missed. |
| `preview` | Supported | Cut decision + source → bounded join MP4 with matching audio | Specialist preview | [Synchronized join test](tests/test_tilt.py) | Join quality and removed context need human review. |
| `timeline-changes` | Supported | Approved cuts + single uncut source timeline → kept spans | Yes | [Native timeline handoff test](tests/test_tilt.py) | Requires exact source hash and separate timeline approval before render. |

Synthetic [tests](tests/test_tilt.py) exercise thresholding, pending-review status, synchronized cut preview, stale-input rejection, and timeline handoff. Synthetic success does not prove camera-roll detection on arbitrary footage.
