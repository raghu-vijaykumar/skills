# Workflow precheck and reviewed plan

**Status:** Complete

**Input:** A mandatory Content Studio precheck inside the workflow skill, with system benchmarks, route recommendations, editable steps, explicit human review, and an execution checklist.

## User scenarios

1. **Before editing (P1):** An editor sees source and system findings, likely routes, time estimates, outputs, risks and review points before full production starts.
2. **Revise the route (P1):** A user changes any planned production step; the editor incorporates it and presents the current plan again. No editing begins until explicit approval of that revision.
3. **Execute the approved steps (P1):** The workflow follows the checklist generated from the approved plan. Plan changes invalidate approval, and package approval requires completed evidence.
4. **Costly enhancements (P2):** Upscale and color routes use short measured samples, source diagnosis and bounded previews. AI inference time is unknown until a representative pilot; optional frame streaming is review support.

## Requirements

- Keep precheck within `content-studio-workflow`, and state the mandatory gate in `AGENTS.md` and direct specialist instructions.
- Record system tools, CPU, RAM, disk and available GPU; probe representative media when supplied. Bound benchmark work and label extrapolations.
- Store an editable plan per draft, including steps, routes, outputs and acceptance criteria. Preserve a separate approval bound to the exact plan content.
- Generate the step checklist from the approved plan; edits require another human review and reset checklist state. Required source and final-render review steps cannot be omitted.
- Reject unapproved or stale plans before workflow commands and reject incomplete plan checklists at package approval and verification.
- Keep lifecycle checklist, subjective media review and publishing authorization as independent gates.

## Acceptance

- Tests prove missing/stale approval and incomplete checklist block execution or package approval.
- Tests prove a revised plan requires reapproval and resets its checklist.
- A bounded media profile reports measured FFmpeg timings separately from unmeasured AI throughput.
- Documentation and the installed skill set pass the repository docs check.
