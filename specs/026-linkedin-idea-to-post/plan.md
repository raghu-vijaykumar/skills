# Implementation Plan: LinkedIn idea to post

**Branch**: `main` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Add an independently discoverable LinkedIn skill and a file-backed CLI state machine. Extend the existing production precheck with a social kind. Keep media production replaceable per post, with optional Remotion content card and code-driven video routes. Keep reusable visual presets in the personal workspace and authorship/review decisions in each draft. Add a personal OAuth publisher using versioned Posts, Images, Documents and Videos APIs.

## Technical context

Node 22 ESM CLI, Python precheck, Remotion content renderer, JSON draft records, Node tests and Python unittest. Default draft root is `C:\workspace\content\linkedin-personal`; callers can override it. No remote database or background service is required.

## Constitution check

- Canonical implementation stays in this repository; the global installer discovers the new skill.
- Existing rendered-evidence and user review gates remain in force.
- All paths and themes are inputs; no Revise Labs dependency is required.
- CLI and contract changes receive tests and docs. A real API post needs separate user authorization.

## Interfaces and data flow

`content-studio linkedin connect|new|status|resume|approve|publish` is the public command group. `new` stores the idea and initializes a social precheck. The agent completes the plan and four review checkpoints through durable stage records. `approve --stage angle|draft|final` records the user's explicit decision against hashes. `publish` is read-only without `--confirm`; confirmed posting verifies precheck and all approvals before an API request.

A draft owns `idea.md`, `brief.json`, `sources.json`, `post.md`, `creative.json`, one optional final `image.png`, `animation.gif`, `carousel.pdf`, or `video.mp4` with `cover.png`/`captions.srt`, `.content-studio/preflight/`, `linkedin-state.json` and `linkedin-receipt.json`. Media is ignored by a generated workspace `.gitignore`. `presets/<slug>.json` can define a reusable project style; its hash is included in angle approval. The stage record tracks hashes and is independent of any chat.

Text posts skip rendering. Image posts can use the existing 1080×1350 card renderer or another approved method; animated images use a 2–250 frame GIF. Information carousels use a multi-page PDF document post; the optional assembler converts reviewed 1080×1350 slide PNGs. Video posts may use the existing Remotion authoring pipeline and exact-master checks. The skill owns research, authorship and visual decisions between CLI review stops; the CLI owns deterministic validation, authentication and posting.

OAuth uses an external developer app with `openid profile w_member_social`. Tokens live in an ignored local secrets file. The publisher uploads PNG/GIF images, PDF documents or videos first, waits for document/video readiness, then sends one Posts API create request. Organic personal posts use a document post for the swipeable information carousel because LinkedIn's Carousel API is sponsored-only. It records an attempted state before that request and will not automatically repeat it after an ambiguous result.

## Verification

Exercise social precheck, preset invalidation, cross-chat resume, required assets, dimensions/duration/pages, OAuth state and token expiry, API uploads and idempotency with fixtures. Run `npm run check:docs`, the workflow Python tests and `npm test`. Inspect delivered sample media at final size. Review the staged diff, commit and push on `main`.
