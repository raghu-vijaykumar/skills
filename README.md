# Skills

Agent skills used by [opencode](https://opencode.ai). Each skill is a folder with a
`SKILL.md` (frontmatter `name` + `description`, then the instructions) plus any scripts
it needs.

| Skill | Purpose |
| --- | --- |
| [hairline-create](hairline-create/SKILL.md) | Create one self-contained interactive isometric line figure with the bundled Hairline engine |
| [learning-engineer](learning-engineer/SKILL.md) | Build and review concepts in the separate local Study knowledge base |
| [content-helper](content-helper/SKILL.md) | One workspace per YouTube channel: public YouTube backups with exact metadata and source in Git, video and asset storage on Drive, editable drafts, intro prepending, analytics, and media extraction |
| [video-idea-engine](video-idea-engine/SKILL.md) | Turns that analytics dataset into a researched, packaged video idea and a production brief: research sweep, scored selection, packaging before production, then a measurement loop |
| [videogen](videogen/SKILL.md) | Reusable Remotion rendering, validation, themes, video/post exports, and YouTube publishing |

`skills-lock.json` records the upstream source of the Hairline skill.

## Install

Clone next to your projects and register the path in your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["C:/workspace/skills"] }
}
```

Or copy a single skill folder into `~/.config/opencode/skills/`.

`videogen` also ships as the npm package at this repository root. Pin a tested Git tag in a content project's `package.json`, run `npm install`, then `npx videogen sync-skill` to install the matching skill in `.agents/skills/videogen` for Codex and OpenCode. New projects can start with `npx videogen init <directory>`; add a draft with `npx videogen scaffold <id> --title "Working title"`.
