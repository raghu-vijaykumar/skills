# Clip selection data model

The draft stores selection evidence in `.content-studio/clipping/`. All timestamps in the selection are absolute source seconds until the delivery timeline resolves them to output time.

| Record | Required fields | Purpose |
| --- | --- | --- |
| Source | relative path, SHA-256, duration, frame rate, dimensions, color/transfer, audio presence | Bind every decision to the finished long-form input. |
| Candidate | ID, source in/out, observed hero description, evidence frame IDs, story beat notes, sound boundary notes, status | Compare possible excerpts without claiming sampled frames are exhaustive. |
| Selection | chosen candidate ID, exact in/out, reviewer decision, source hash | Freeze the editorial range for the preflight and timeline handoff. |
| Crop interval | source in/out, normalized x/y/w/h, subject evidence IDs, method ID, status | Keep a stable portrait crop for each reviewed interval. |
| Review | artifact paths, reviewer decision, unresolved defects | Keep the source/crop comparison and decision traceable. |

The selection record is a proposal. The approved preflight plan and immutable delivery timeline remain the production authority. Changing the source, selected range, or crop creates a revised proposal and requires the relevant human review again.
