# Implementation Plan

1. Inventory YouTube backup IDs, source metadata, Git state, and generated media. Record a one-to-one migration map before copying.
2. Move channel source and assets into `content/revise-labs`, with per-video source beside the public backup or under `drafts/`; keep generated media ignored from Git.
3. Extend content-helper with exact public metadata, ID-based draft handoff, Drive verification, and selective Git publishing. Keep the idea engine targeting the same draft layout.
4. Add a reusable YouTube publish command to videogen; use project configuration for credentials and optional project gates. Record the returned ID for later backup.
5. Remove duplicate shared implementations and obsolete publishing from Revise Labs after the new content project and skill prove the workflow. Update owner documents.
6. Run focused and repository checks, clean install tests, and a representative Studio/range review. Commit and push tested batches; pin the skills tag in the content project.
