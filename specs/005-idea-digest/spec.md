# Feature Specification: digest-backed idea discovery

**Created:** 2026-11-01
**Status:** Complete

## User scenario

The globally installed video-idea-engine skill can collect recent engineering, AI, research, science, and GitHub leads into a structured digest, compare them with channel analytics, and use selected leads to seed one draft's research sweep. Digest headlines are candidate leads; the idea brief must still verify claims against primary sources.

## Requirements

- Move the standalone digest fetchers and curated source catalog from the retired Revise Labs checkout into `video-idea-engine`, with the skill repository as canonical code source.
- The default action writes machine-readable, dated leads under the channel workspace's `analysis/digest/` and sends no message. A readable preview is available. Telegram delivery remains optional and requires an explicit command and credentials.
- Resolve channel-specific credentials and sent-item state from the content workspace, never from the skill repository. Preserve the existing ignored `.env` and modified sent-history bytes during migration.
- The idea planner can include an explicitly supplied digest snapshot as labeled, unverified leads in `research.md`; it must not treat headlines or popularity scores as proved technical claims.
- Remove the old digest code and root npm command from the retired snapshot after the skill copy, local state, and credentials are verified. Keep unrelated local edits untouched.

## Acceptance

- Tests cover RSS/JSON output, source failures, no-send default, explicit send protection, and planner lead labeling.
- A real limited source sweep writes dated JSON without Telegram delivery. The skill works from both global installation paths with its own locked dependencies.
- Skill validation, docs checks, clean Git diffs, selective commits, pushes, and remote HEAD checks pass.
