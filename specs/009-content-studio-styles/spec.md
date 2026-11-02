# Content Studio style discovery

**Created:** 2026-11-02
**Status:** Complete

## Contract

Add `content-studio-styles` as the eighth globally discoverable Content Studio skill. It lists current built-in styles from the shipped runtime registry, their formats and uses, and the built-in themes separately. For a selected project, it reports the styles enabled by `videogen.config.ts` through the existing `videogen styles` command and includes project-defined custom styles. Listing never edits a preset or draft.

Keep theme (brand), style (editorial treatment), and renderer distinct. Preserve the existing videogen package name, CLI, and consumer exports. Release a new immutable tag, pin it in the active content repository, and keep individual video folders untouched.

## Acceptance

The built-in list includes Core Explainer, Tech Dispatch, Evidence Lab, and Hairline; Evidence Lab shows its firsthand-evidence requirement and Hairline is video-only. The neutral starter project lists only its configured style, while Revise Labs lists four. Eight skill folders validate and install without duplicates. Package, content, and docs checks pass from clean tagged installs; remote heads are verified.
