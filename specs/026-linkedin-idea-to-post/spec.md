# Feature Specification: LinkedIn idea to post

**Branch**: `main` | **Created**: 2026-11-18 | **Status**: Approved for implementation

## User journeys

### P1: Resume a personal post from any chat

Given a rough opinion, notes, links or owned assets, Content Studio creates a draft in a separate personal workspace. It records the user's stance, verifiable claims, sources, audience, language, proposed format, visual identity and exact review state. Another chat can resume by draft ID without relying on prior chat history.

**Acceptance**: Intake recommends text, an image, animated image, information carousel or video with a reason. A reusable project preset can be chosen for the post, while the production method can change for each idea. No production proceeds before the approved precheck and angle. Changed inputs or a changed preset invalidate later approvals.

### P2: Produce and review the exact edition

The studio researches factual claims without inventing personal experience, drafts first-person LinkedIn copy and the chosen visual treatment, then pauses for draft approval. It exports a text-only post, 1080×1350 image or animated GIF, multi-page portrait PDF document carousel, or 45–90 second 1080×1350 video. Narration, preset and production method are chosen per idea. The exact final copy and media receive a separate final review.

**Acceptance**: A text-only post needs no media. Original illustrations are identified as such, not falsely labelled evidence. Carousel review includes every slide and the full PDF. Animated GIF review includes the full motion. Video review includes hero elements, full export, captions for narration, cover and mobile safe areas.

### P3: Publish only the approved package

The studio connects a member through OAuth, previews an exact dry-run package and posts through LinkedIn's versioned API only after an explicit publication request. Credentials stay outside Git. It saves receipts and prevents a duplicate post after an uncertain response.

**Acceptance**: Text, image/GIF, document carousel and video routes use the correct upload steps. Expired or insufficient access stops safely. A changed copy or asset fails hash verification. A published ID is retained.

## Requirements

- Four human decisions: angle/format and plan, draft, exact final package, separate publication authorization.
- English and any professional topic by default; personal, Revise Labs or project presets and narrated or silent video are chosen per idea.
- Stable intake, review and publishing contracts accept final media from different production methods per post. WhatsApp is outside this first release.
- Durable draft/checkpoint files under a separately configurable personal content workspace.
- Direct personal-profile posting uses `w_member_social`; no credentials or generated media in this bundle.
- Public CLI, content contract and skill changes receive tests and documentation; preserve existing video behavior.

## Success criteria

- A fresh chat can resume a draft from disk and report the next required review.
- No confirmed publish path runs with stale plan, draft or final approval.
- Mocked API tests cover all five formats and uncertain-response reconciliation.
- A real LinkedIn post remains unverified until the user explicitly authorizes a test post on a connected account.
