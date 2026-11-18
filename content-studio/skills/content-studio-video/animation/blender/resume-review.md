# Resumable Blender render review

The [version 2 clamp smoke specification](examples/clamp-contract-v2.json) was rendered twice in Blender 5.3 at 320×240, 24 fps, for three frames. One run stopped after its first PNG and resumed in a new Blender process; the other rendered all three without a stop. Both used the same builder and imported helper dependency.

| Check | Observed result |
| --- | --- |
| Interrupted state | Manifest contained one hashed PNG; no MP4 or completion marker existed. |
| Resume | Two missing frames rendered; all three frame hashes were checked before encoding. |
| Exact output | Both MP4s decode to three frames at 320×240 and have the same SHA-256: `e0dc1e05b54720066cac9c84291c8abf855c6d207bc6ad53aa58b5891c1ad165`. |
| Frame comparison | Decoded image pixels in the three PNGs match across runs. The PNG file bytes differ, so cache integrity uses each run's own recorded file hash. |
| Repeated resume | Completion marker recheck preserved the delivered MP4 hash and did not render another frame. |
| Input signature | Both final-code runs recorded `2075f5d272d4d05e1fc8b829bb75720ea84041b7ca2af26d315f21deacfaab38`, including builder, spec, helpers, and renderer source. |

Unit tests also reject a changed input signature, missing or modified cached frame, and insufficient free space. The frame cache keeps `manifest.json`, `render.log`, `complete.json`, and every PNG after the encode for diagnosis. No source or review evidence is deleted automatically. This is a small synthetic smoke test; future high-resolution routes still need a bounded frame-cost benchmark and exact rendered review.
