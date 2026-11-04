---
name: content-studio-workflow
description: Run a resumable, retryable, checkpointed Content Studio workflow from one prompt JSON, preserving human approvals.
---
# Content Studio Workflow
Run `python content-studio/skills/content-studio-workflow/scripts/workflow.py --prompt content-studio/examples/vlog-workflow.json`. The workflow stores durable step state under `.content-studio/workflow/state.json`, uses input/config hashes to invalidate stale steps, and retries transient command failures. `--resume` reuses successful steps; `--reset-step STEP` invalidates a step and descendants. `--status` shows progress.

Only explicitly configured commands execute. Each step can declare dependencies, a command array, output files, retries and `approval_required`. Approval checkpoints stop execution until a human supplies an approval record with the expected input fingerprint; do not auto-approve. Publication always requires separate explicit authorization and is not an automatic workflow step. Inputs and originals are never overwritten by this runner. Do not use shell strings, and do not store API keys or voice samples in the prompt.
