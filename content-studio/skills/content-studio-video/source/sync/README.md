# Separate-recorder sync capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `sync-recorder` | Supported | Camera/manual edit + recorder → hashed offset/drift report and bounded stereo audition | `external-sync` cue on one uncut SDR manual edit | Synthetic delay, drift, silence and ambiguity tests | Needs shared active audio; uncertain matches stop for human review. Raw-camera results do not transfer across manual cuts. |
