# Data model

## Skill entry

- `name`: globally unique, lowercase, hyphenated identifier from YAML frontmatter.
- `path`: bundle-relative directory containing `SKILL.md`.
- `kind`: lifecycle, category router, leaf operation, or compatibility entrypoint.
- `dependencies`: existing bundle modules and external tools, stated by the skill.
- `methods`: implemented method descriptors for leaf operations.

## Method descriptor

- `id`: stable operation-local ID.
- `script`: bundle-relative executable entrypoint; distinct for each implemented alternative.
- `status`: supported or unsupported; unsupported entries do not expose a runnable script.
- `inputs`, `outputs`, `review`: plan fields required before production editing.

## Draft workflow state

The existing `.content-studio/preflight/` plan and checklist remain authoritative. A new stage or changed method invalidates approval. The manually rendered edit hash is the time reference for narration and overlays; voice, upscale, and graphics outputs retain their own hashes and review records.
