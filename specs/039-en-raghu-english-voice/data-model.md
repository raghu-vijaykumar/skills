# Data Model: en-raghu English Voice

`profile.json` retains schema version 1 and the existing consent and sample fields. For the English backend it adds:

- `backend.name`: `ChatterboxTurbo`.
- `backend.model_id` and `backend.revision`: official checkpoint identity.
- `references`: map of variant name to `{file, sha256, duration_seconds}`.

The two `samples` entries point to the same consented WAV files. A reference may be chosen only when its file exists inside the resolved profile folder and matches its declared hash. The narration manifest's `params` captures the chosen variant and reference hash; changing either invalidates reuse.
