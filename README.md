# Content Studio skills

This repository is the editable source of the `content-studio` video lifecycle bundle. The npm package remains `@raghu-vijaykumar/videogen` so existing Remotion imports and the `videogen` CLI keep working. Its canonical source is under [content-studio](content-studio/).

| Skill | Use |
| --- | --- |
| [content-studio](content-studio/skills/content-studio/SKILL.md) | Route one draft through the lifecycle |
| [content-studio-ideagen](content-studio/skills/content-studio-ideagen/SKILL.md) | Owned analytics, public comparisons, digest, idea brief |
| [content-studio-videogen](content-studio/skills/content-studio-videogen/SKILL.md) | Narrated Remotion videos, themes, Hairline style, render review |
| [content-studio-videopreprocess](content-studio/skills/content-studio-videopreprocess/SKILL.md) | Capture ordering, footage cleanup, blur and Dolby Vision review |
| [content-studio-videoedit](content-studio/skills/content-studio-videoedit/SKILL.md) | Clip editing or manual export review, transcription, captions, thumbnail |
| [content-studio-publish](content-studio/skills/content-studio-publish/SKILL.md) | Reviewed package approval, YouTube now/schedule, Instagram now |
| [content-studio-archive](content-studio/skills/content-studio-archive/SKILL.md) | Independent public backup, Drive verification, monthly reconciliation |

## Install

Clone this repository, then run `node content-studio/scripts/cli.mjs install-skills --global`. The installer stores one versioned bundle at `~/.agents/content-studio/v<version>` and links its seven skill folders directly under `~/.agents/skills`. [Codex](https://learn.chatgpt.com/docs/build-skills) and [OpenCode](https://opencode.ai/docs/skills) both discover that global path. It verifies the seven matching skill entrypoints, refuses to replace unmanaged folders, then removes the obsolete global names `videogen`, `content-helper`, `video-idea-engine`, `hairline-create`, `learning-engineer`, and the superseded `content-studio-ideas`, `content-studio-animate`, and `content-studio-vlog`.

A video project can pin a tested Git tag of this private repository in `package.json`, run `npm install`, and use `npx videogen sync-skill` to install the matching animation skill locally. `npx videogen init <directory>` starts a project and `npx videogen scaffold <id> --title "Working title"` creates a draft. The root npm package includes only `content-studio/`.

The digest and channel helper are internal tools in the bundle, not separately discoverable skills. The Hairline style adapts the MIT licensed [Hairline](https://github.com/lucasmarkes/hairline) visual rules; the source attribution is retained in `content-studio/styles/hairline-source/LICENSE`. Channel media, drafts, secrets, and analytics stay in each content workspace.
