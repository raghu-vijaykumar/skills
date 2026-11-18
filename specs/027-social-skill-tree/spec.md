# Feature Specification: Content Studio Social skill tree

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: Ready for implementation

## User journeys

### P1: Find the right social workflow

From any chat, a user can invoke Content Studio Social and select YouTube, LinkedIn or Instagram work by purpose. Independently callable leaves distinguish publication from analytics. The LinkedIn idea-to-post workflow remains reachable by its existing skill name.

**Acceptance**: Recursive skill discovery finds the Social entrypoint and platform leaves. Existing skill links still resolve, and no duplicate publishing implementation is introduced.

### P2: Publish through the existing platform gates

YouTube publishing and scheduling, LinkedIn personal posting, and Instagram Reel publishing route to their existing approved packages, dry runs, explicit authorization, and receipts.

**Acceptance**: New skills point to the owning commands and preserve the existing review and retry rules. No skill treats analytics access or an approved draft as publication permission.

### P3: Inspect platform analytics honestly

YouTube analytics uses the existing owned-channel collector. LinkedIn and Instagram analytics have independently callable analysis guidance for account exports or authorized data available in a chat, without claiming live collectors that this repository does not have.

**Acceptance**: Each analytics skill identifies its data source, collection time, metrics actually present, and unavailable fields. Public comparison figures remain public estimates, not private reach, CTR, VTR, or retention.

## Requirements

- Canonical skill guidance lives under `content-studio-social/` with platform and operation folders. Existing names remain compatibility routes where needed.
- Use one canonical publishing implementation per platform; skills route to existing CLI/scripts.
- Keep the mandatory production precheck and separate publication authorization.
- Keep analytics and credentials outside Git. This release organizes and routes; it adds no live LinkedIn or Instagram analytics collector.
- Update discoverability docs, tests, and versioned installation.

## Success criteria

- An agent invoking Social can choose the correct leaf on first read.
- Every new leaf is independently discoverable after install.
- Docs and skill-discovery checks pass; previous publication commands remain functional.
