# Feature Specification: consolidate personal skills

**Created:** 2026-10-27
**Status:** Complete

## User scenarios

- A new workspace can discover Hairline and Study guidance from the global skill install while the canonical files remain in `raghu-vijaykumar/skills`.
- The retired Revise Labs checkout no longer holds duplicate skill copies.

## Requirements

- Preserve Hairline's source and provenance and all supporting scripts, examples, and templates.
- Keep Learning Engineer tied to the separate Study knowledge base, with portable references to its own templates.
- Keep the repository-root npm package scoped to `videogen/`.
- Validate both skills and install them before deleting legacy copies.
- Preserve unrelated digest state, credentials, and user edits in the retired checkout.
