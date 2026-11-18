# SFX capability matrix

The shared stock catalogue owns the 252 pinned Earshot WAVs. Technical audit,
listening approval, video cue approval, and final output review are separate gates.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `earshot-bank-import` | Supported | Pinned Earshot revision → 252 WAVs, metadata, and gallery | Library asset | [Bank test](tests/test_sfx.py) and [audition gallery](../../stock-library/assets/earshot-gallery.html) | 16 technical audit failures stay unavailable; all sounds need listening review. |
| `sfx-forge` | Supported | Earshot recipe and parameters → original candidate and recipe | Pending candidate | [Workflow](references/workflow.md) and [import script](scripts/sfx.py) | Optional Earshot creation dependencies are needed; output needs audit and listening review. |
| `sfx-fit` | Supported | Licensed recording → fitted candidate and recipe | Pending candidate | [Workflow](references/workflow.md) and [import script](scripts/sfx.py) | Derivative inherits source license; Git shipment needs redistribution rights. |
| `sfx-events` | Supported | Edited video or scene plan → evidence-linked event manifest | Proposal only | [Event tests](tests/test_sfx.py) and [analyzer](scripts/events.py) | Edited cut meanings need actual frame and audio review. |
| `sfx-propose` | Supported | Event manifest, catalogue, optional music bed → pending SFX or no-effect cues | Pending cues | [Proposal tests](tests/test_sfx.py) and [workflow](references/workflow.md) | Music events require a separate bed; final cues need human approval. |
