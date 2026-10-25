# Skills

Agent skills used by [opencode](https://opencode.ai). Each skill is a folder with a
`SKILL.md` (frontmatter `name` + `description`, then the instructions) plus any scripts
it needs.

| Skill | Purpose |
| --- | --- |
| [youtube-channel-backup](youtube-channel-backup/SKILL.md) | Incremental YouTube channel backup into per-video folders, mirrored to Google Drive with rclone |

## Install

Clone next to your projects and register the path in your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["C:/workspace/skills"] }
}
```

Or copy a single skill folder into `~/.config/opencode/skills/`.
