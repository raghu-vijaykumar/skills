# Skill discovery contract

1. Search `content-studio/skills/` recursively for files named exactly `SKILL.md`.
2. Read `name:` and `description:` from frontmatter. Reject missing or duplicate names and any name that is not lowercase letters, digits, or hyphens.
3. Link each discovered folder as a direct child of the managed install's `skills/` directory, using its frontmatter name.
4. Refuse unmanaged destinations. Replace only links into managed Content Studio releases.
5. Verify every installed link resolves to the expected source folder and frontmatter name. Root compatibility skills are discovered like other skills.
6. Do not discover `UPSTREAM-SKILL.md` or folders without an exact entrypoint.
