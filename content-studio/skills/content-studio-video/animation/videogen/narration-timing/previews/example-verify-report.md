# Narration timing example

Illustrative output example. `narration.mjs` builds timed cues; `verify-narration.mjs`
checks the exact authored phrases against the recorded audio and fails on a mismatch.

```powershell
node content-studio/skills/content-studio-video/animation/videogen/narration-timing/scripts/narration.mjs <project>
node content-studio/skills/content-studio-video/animation/videogen/narration-timing/scripts/verify-narration.mjs <project>
```

A changed script or voice recording invalidates the cue cache. Review synchronization
in the rendered motion, not only in the JSON.
