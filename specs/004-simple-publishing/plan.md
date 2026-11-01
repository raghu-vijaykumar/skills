# Plan: simple video publishing

1. Keep the existing YouTube upload and native `publishAt` path; expose explicit platform selection and reject Instagram scheduling.
2. Port the proven Reel normalization and Meta container flow into a generic `videogen` script. Use direct local upload, status polling, and draft receipt checkpoints; omit R2/Catbox hosting and the retired queue.
3. Add project-configured Instagram token path, agent guidance, and focused mocked tests. Pin a new Git tag in the active content repo.
4. Remove archived publisher code and queue scripts from the legacy checkout, keeping the news digest and its unrelated edits. Update owner docs and verify all repositories.
