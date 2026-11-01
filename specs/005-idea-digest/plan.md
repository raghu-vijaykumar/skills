# Plan: digest-backed idea discovery

1. Copy the tracked digest fetchers and curated YAML into `video-idea-engine/digest/`, excluding local state and secrets.
2. Make the default CLI output structured research leads; keep a preview and an explicit optional Telegram send. Store outputs and sent history under the chosen channel workspace.
3. Let `plan.py` append an explicitly supplied digest snapshot as unverified research leads. Update the skill instructions and tests.
4. Preserve and hash-check the old ignored credentials and modified sent history in the active content workspace. Remove the retired code and update owner docs.
5. Install the skill and its locked dependencies globally, validate a limited live sweep and clean project discovery, commit and push scoped changes.
