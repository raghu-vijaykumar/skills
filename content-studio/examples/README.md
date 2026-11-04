# Prompt-driven vlog workflow (initial scaffold)

1. Copy `vlog-workflow.json` to your own configuration and create the workspace folder specified in `workspace`.
2. Place the raw video at `<workspace>/original/my-vlog.mp4`; copy `context.json` to `<workspace>/context.json`.
3. Set the video path, facts, language, mute/keep-original-voice decisions, upscaling preference, and human review requirements in the JSON. Do not store credentials or voice samples here.
4. Run from the repository root: `python content-studio/skills/content-studio-workflow/scripts/workflow.py --prompt content-studio/examples/vlog-workflow.json --resume`.
5. Inspect `<workspace>/.content-studio/understanding/evidence.json` and frames. A vision-capable agent must generate factual observations and a timed narration proposal; this semantic step is not yet wired automatically.
6. To approve a gate, inspect its review materials and create `<workspace>/.content-studio/workflow/approvals/<step-id>.json` with `{"approved":true,"fingerprint":"<printed fingerprint>"}`. This approval must be authored by a human, never automatically by the agent. Re-run `--resume`.
7. Use `--status` to inspect state and `--reset-step STEP` to invalidate a stage and downstream stages.

**Current limitations:** This example is a proof-of-concept DAG, not a fully integrated publish pipeline. The understand command extracts frames, not semantic descriptions or spoken narration. Voice synthesis is deferred until consented samples and a reviewed local backend are available. Publishing is always separate and explicitly authorized.
