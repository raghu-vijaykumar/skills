# Skills

Agent skills used by [opencode](https://opencode.ai). Each skill is a folder with a
`SKILL.md` (frontmatter `name` + `description`, then the instructions) plus any scripts
it needs.

| Skill | Purpose |
| --- | --- |
| [content-helper](content-helper/SKILL.md) | One workspace per YouTube channel: incremental backup of public/private/scheduled uploads to Google Drive, local drafts kept in sync, intro prepend, local pruning that never touches Drive, and retention/analytics reports |

## Install

Clone next to your projects and register the path in your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["C:/workspace/skills"] }
}
```

Or copy a single skill folder into `~/.config/opencode/skills/`.
