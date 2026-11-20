# Long cut

The long cut planner assembles ordered camera originals after review of technical cut candidates. It does not choose a story, remove spans without a human decision, or approve the final render.

**Status:** `Supported` means the method has a runnable script. **Delivery timeline:** `Specialist only` means the planner prepares a reviewed timeline proposal; the native timeline handles the final picture encode after its own approval.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `long-cut-propose` | Supported | Ordered originals and blur, pan, tilt reports → source-linked candidate proposal | Specialist only | [Workflow and review gates](SKILL.md) | No candidate is an approved removal. |
| `long-cut-build` | Supported | Complete human decisions and approved plan → versioned delivery timeline proposal | Specialist only | [Long cut tests](tests/test_long_cut.py) | SDR picture only; final render needs separate human timeline approval. |

## Evidence note

The skill's tests use synthetic media and source-linked decisions. A passing planner test does not replace picture and audio review of a real long cut.
