# Fast pan cuts capability matrix

The scanner proposes sustained rapid camera-motion ranges; an editor selects exact frames and reviews a short cut with synchronized audio. Approved removals become source spans in the existing delivery timeline. The small synthetic example demonstrates the mechanics, not a reliable aesthetic decision on all footage.

**Status:** `Supported` means the manifest provides a runnable script. `Unsupported` means no script is provided. **Delivery timeline:** `Yes` means the one-render timeline consumes an equivalent operation; `Specialist only` means a bounded preview is outside that renderer; `No` means the operation is diagnostic or unsupported.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `scan` | Supported | SDR CFR video → source-linked motion candidates | No | [Synthetic scan report](previews/scan-report.json) | Global motion can flag intentional tracking or moving foreground; all candidates await frame review. |
| `preview` | Supported | Cut decision + source → bounded MP4 with matched picture/audio trims | Specialist only | [Synthetic cut comparison](previews/fastpan-cut.gif) | Small SDR preview only; an abrupt join or damaged speech needs a revised cut or SKIP. |
| `timeline-changes` | Supported | Human-approved cuts + uncut source timeline → kept source spans | Yes | [Synthetic changes file](previews/changes.json) | No final render or approval; refuses an existing timed edit and depends on native timeline validation. |

## Evidence note

The [rebuild note](previews/evidence.md) identifies the synthetic source, exact commands, preview boundaries, and review status. No Dubai footage or private audio is committed. Run the [behavioral tests](tests/test_fastpan.py) to verify the scan, synchronized picture/audio preview, stale-input rejection, and native timeline handoff. The GIF is illustrative; it is not an approved delivery result.
