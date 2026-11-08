# Research: migration seams

- **Installer**: `content-studio/scripts/install-skills.mjs` currently hardcodes 18 direct-child skill names and links those folders. Decision: recursively discover exact `SKILL.md` files, validate unique frontmatter names, and link each by that name. Preserve unmanaged-link refusal and managed release checks.
- **Docs validator**: `content-studio/scripts/check-docs.mjs` also hardcodes direct children. Decision: use the same recursive discovery contract and validate all nested links.
- **Npm runtime**: `package.json` points build, tests, bin, and exports to `content-studio-videogen`. Decision: change internal paths to the moved source while keeping package export names and `videogen` executable stable.
- **Relative paths**: Python modules and Node scripts refer to siblings through `parents[n]` and relative imports. Decision: resolve the bundle root by locating its named ancestor or use a tested shared helper, then update sibling paths after moves.
- **Compatibility**: Existing content projects may call old script paths. Decision: retain small root dispatchers for documented public CLIs and old skill names; no duplicate implementation copies.
- **Future methods**: the proposal names deblur, AI upscale variants, and detailed 3D operations beyond today's backends. Decision: expose only working methods; mark future entries `UNSUPPORTED` in docs and registries.
- **Default workflow**: current router suggests AutoCut and per-clip upscale. Decision: raw folder means source prep only; AutoCut explicit-only; post-edit voice and full-master upscale precede overlays.
