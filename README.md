# Skills

Agent skills used by [opencode](https://opencode.ai). Each skill is a folder with a
`SKILL.md` (frontmatter `name` + `description`, then the instructions) plus any scripts
it needs.

| Skill | Purpose |
| --- | --- |
| [content-helper](content-helper/SKILL.md) | One workspace per YouTube channel: incremental backup of public/private/scheduled uploads to Google Drive, local drafts kept in sync, intro prepend, local pruning that never touches Drive, analytics dataset collection, and audio/frame/clip extraction |
| [video-idea-engine](video-idea-engine/SKILL.md) | Turns that analytics dataset into a researched, packaged video idea and a production brief: research sweep, scored selection, packaging before production, then a measurement loop |
| [videogen](videogen/SKILL.md) | Reusable Remotion rendering, validation, themes, and video/post exports |

## Install

Clone next to your projects and register the path in your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["C:/workspace/skills"] }
}
```

Or copy a single skill folder into `~/.config/opencode/skills/`.

`videogen` also ships as the npm package at this repository root. Pin a tested Git tag in a content project's `package.json`, run `npm install`, then `npx videogen sync-skill` to install the matching skill in `.agents/skills/videogen` for Codex and OpenCode. New projects can start with `npx videogen init <directory>`.
