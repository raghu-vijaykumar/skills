# Retime capability matrix

Each method starts with a baseline and finite frame-aligned proposal, then a
bounded picture/audio preview. A pending review cannot be fingerprinted for
final render. The exact master records the delivered frame count and review
samples; human motion and sound review remains required.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `speed` | Supported | SDR source span + 0.25–4× factor + tempo/mute → resolved frames and shifted cues | Yes | [Rendered speed and audio fixture](../../timeline/tests/test_retime.py) and [review method](references/retime.md) | Effective factor snaps to frames; review cadence and sound. |
| `freeze` | Supported | One SDR source frame + finite hold + mute → held frames and shifted cues | Yes | [Rendered freeze and exact-master fixture](../../timeline/tests/test_retime.py) and [review method](references/retime.md) | Hold is frame-aligned and at most 10 seconds. |
| `reverse` | Supported | SDR source span + reverse/mute audio → reversed frames and shifted cues | Yes | [Rendered reverse and audio fixture](../../timeline/tests/test_retime.py) and [review method](references/retime.md) | At most 15 seconds and 512 MiB estimated picture buffer. |
| `loop` | Supported | SDR source span + count 2–8 + repeat/mute audio → finite repeated frames and shifted cues | Yes | [Rendered loop and audio fixture](../../timeline/tests/test_retime.py) and [review method](references/retime.md) | At most 10-second source, 60-second output and 256 MiB estimated picture buffer. |
