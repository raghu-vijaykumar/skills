# Declarative vlog prompt

Edit only `vlog-workflow.json`: `video` (an existing approved master), `workspace`, `voiceover`, `editing`, and `publish`. No command arrays, inputs/outputs, dependencies or retry settings are required.

From the repository root:

```bash
python content-studio/skills/content-studio-workflow/scripts/workflow.py --prompt content-studio/examples/vlog-workflow.json --resume
```

The runner creates internal stages and saves progress under `<workspace>/.content-studio/workflow/state.json`. Use `--status` to inspect state and `--reset-step STEP` to invalidate a stage.

**Scope today:** the executable voiceover stage extracts sparse frames and evidence; vision interpretation, script generation, approved audio synthesis and timeline mixing are not yet wired. A review checkpoint is not a substitute for a generated script. Voice cloning remains unconfigured until consented samples and a reviewed backend are supplied. Editing preferences are captured but not yet executed by the simplified runner. No publishing occurs automatically.

For a human approval gate, inspect the actual artifact, then create `<workspace>/.content-studio/workflow/approvals/<step-id>.json` containing `{"approved":true,"fingerprint":"<printed fingerprint>"}`. The agent must never create human approval records.
