---
name: content-studio-workflow
description: Profile a Content Studio draft, agree an editable production plan and checklist with the user, then run a resumable workflow after mandatory human review.
---
# Content Studio Workflow

Before any Content Studio editing or production, run the integrated precheck in `scripts/preflight.py` for the target draft. Profile the current machine and representative media, including bounded decode/Lanczos measurements and honest AI upscale estimates. Draft an editable plan with recommended routes for upscale, color, audio, previews or streamed frames, timing, outputs, and acceptance criteria. Show the full plan to the user, incorporate requested workflow changes, and obtain explicit human approval of the current revision. This review is mandatory and cannot be skipped. Read [precheck planning and benchmarks](references/planning.md).

After approval, `preflight.py` generates the exact step checklist from the reviewed plan. Run `verify --phase start` before editing, update each step with evidence, and run `verify --phase complete` before package approval. A plan edit invalidates approval and requires another human review. The lifecycle checklist and publish authorization remain separate gates. Direct specialist editing calls also start here.

Run `python content-studio/skills/content-studio-workflow/scripts/workflow.py --prompt content-studio/examples/vlog-workflow.json`. Each command step must declare `plan_step` matching an approved plan item. The workflow stores durable step state under `.content-studio/workflow/state.json`, uses input/config hashes to invalidate stale steps, and retries transient command failures. `--resume` reuses successful steps; `--reset-step STEP` invalidates a step and descendants. `--status` shows progress.

Only explicitly configured commands execute. Each step can declare dependencies, a command array, output files, retries and `approval_required`. Approval checkpoints stop execution until a human supplies an approval record with the expected input fingerprint; do not auto-approve. Publication always requires separate explicit authorization and is not an automatic workflow step. Inputs and originals are never overwritten by this runner. Do not use shell strings, and do not store API keys or voice samples in the prompt.
