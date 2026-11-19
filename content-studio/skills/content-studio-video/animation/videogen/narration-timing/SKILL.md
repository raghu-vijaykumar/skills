---
name: content-studio-video-narration-timing
description: Generate and verify narration cues for code-driven videos.
---

# content-studio-video-narration-timing

Before production edits, complete the mandatory `content-studio-workflow` precheck with the exact method, script, outputs, estimate, and review criterion. Use `scripts/narration.mjs` to build timed cues and `scripts/verify-narration.mjs` to check the exact authored phrases and audio. A changed script or recorded voice invalidates the cue cache. Review synchronization in rendered motion.

Before synthesis, run `node content-studio/skills/content-studio-video/animation/videogen/narration-timing/scripts/narration.mjs <draft-folder> --rhythm-only`. It validates authored phrases and writes `assets/generated/audio/narration-rhythm.json` without producing speech. The same advisory report refreshes during normal narration generation. Review runs of similarly long phrases and repeated openings in context; a short phrase should carry a real question, turn, or payoff. For long-form work, review chapter progress as well as individual phrase length. Rhythm suggestions never approve or reject the script.

Record needed but unconfirmed story specifics in the authoring prompt as `unknown` (for example, `ticket_status: unknown`). Do not turn those placeholders into narrated facts. Ask the creator or remove the claim before synthesis; the rhythm report does not verify factual claims.

When a Core Explainer scene plan assigns one cue per scene, run `videogen align-narration <id>` after synthesis. This retains the original generated audio, accelerates only overlong phrases (maximum 1.7×), pads shorter phrases, and updates cue timing to exact frame boundaries. Recheck the narration cache and listen to the rendered audio; rewrite phrases that sound rushed. See [the idea-to-explainer route](../references/idea-to-explainer.md).

Use the [narration review loop](../../../review/critique/references/narration-scoring.md) to compare script beats and performed takes. After a correction, verify the revised word or phrase cues on the rendered picture.
