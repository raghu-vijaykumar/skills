---
name: content-studio-video-narration-timing
description: Generate and verify narration cues for code-driven videos.
---

# content-studio-video-narration-timing

Before production edits, complete the mandatory `content-studio-workflow` precheck with the exact method, script, outputs, estimate, and review criterion. Use `scripts/narration.mjs` to build timed cues and `scripts/verify-narration.mjs` to check the exact authored phrases and audio. A changed script or recorded voice invalidates the cue cache. Review synchronization in rendered motion.

When a Core Explainer scene plan assigns one cue per scene, run `videogen align-narration <id>` after synthesis. This retains the original generated audio, accelerates only overlong phrases (maximum 1.7×), pads shorter phrases, and updates cue timing to exact frame boundaries. Recheck the narration cache and listen to the rendered audio; rewrite phrases that sound rushed. See [the idea-to-explainer route](../references/idea-to-explainer.md).
