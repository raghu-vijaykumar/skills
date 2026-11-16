# Reconstruct a narrated motion reference

Use a full reel or finished video to develop a repeatable method for a new subject. Keep reference picture, original narration, graphics and sound in the analysis workspace. Author the candidate from its own script, assets, voice and effects. Asset titles and layer names are for the project. Use the reference's readable pacing and composition to decide what belongs onscreen.

Begin before a candidate exists. Run `python scripts/survey_reference.py --reference SOURCE --out NEW_PRIVATE_FOLDER` for complete-duration inspection windows, likely cuts, source hash, and an editable actor inventory template. Optional `--region NAME:LEFT,TOP,RIGHT,BOTTOM` flags motion separately in named parts of the square viewing canvas. This pass samples at 8 fps. When a gesture, fall, or switch happens between tiles, trace the relevant frames at their native cadence.

## Checklist for each source and result

| Pass | Evidence to record | Completion criterion |
| --- | --- | --- |
| Source coverage | Exact file hash and duration, complete shot list, independently aligned spoken-word timestamps and regional frame traces | Every reference interval is surveyed. Step through consecutive frames at busy moments, including captions, actor poses, small props, bursts, camera moves and transitions. Label uncertain or obscured details. |
| Object and action inventory | Source in and out, named hero and secondary actors, start and end states, z-order and masks, action and timing, expression and gaze, typography, palette and lighting, sound cue, evidence frame | Split shots at every meaningful change. Record continued motion, swaps, entrances and exits. Track the same actor across a handoff. A motion score or a chapter midpoint does not identify the action. |
| Script and voice | An original spoken line for each beat, spoken-word onset and end from the selected audio, and a read-through | Start with a concrete hook, then make the object, action and consequence audible. Rewrite a wordy or flat phrase before speed-fitting. Check pauses, emphasis, natural delivery and audible sync. Keep raw voice and measured cues together. |
| Asset construction | Layered hero and prop assets with provenance, axes and pivots, expression/gesture poses, independent controls and isolated hero evidence | Draw separate silhouettes, screens, faces or parts. Use 2D paths for flat mechanisms, a rig for joints and expressions, and editable 3D when the shot needs load-bearing depth or perspective. Check contact, occlusion and held states. |
| Word choreography | Each audible word mapped to a visible event and a caption cue, with an actor and concrete change named | Use action words and emphasized nouns for entries, impacts, transfers, feature reveals and emotional turns. Connect short words with an intentional ongoing motion, an expression or an editorial cue, and name the continuity. Review caption-only emphasis separately from meaningful motion. Treat pauses and breath windows as authored holds. |
| Composition and mix | An isolated action render, a narrated shot render and boundary evidence across adjacent shots | Verify the mechanism with a fixed camera first. Apply framing, focus, layer order, typography, movement easing, cuts, expressive poses and original effects on the audio clock. Inspect onset, impact and settle at delivery size, then play with sound at real speed. |
| Exact comparison and revision | Full-range beat map, paired review, ranked action omissions, native-frame evidence and fixed-render rechecks | Use consecutive frames around cues and cuts. Look for edge clips, occluded hands, misplaced focal words, late props, lost identity, frozen expressions, audio masking and missing micro-actions. Diagnose, change, render and retest. Track structural coverage separately from observed motion and creative similarity. |
| Object quality | [Object scores](object-scoring.md) for paired hero and supporting actors, with before/after render evidence and a ranked list of retests | Retest deficits in form, material, staging, mechanics, timing and continuity. An improvement in one axis does not close a deficit in another. |

For a private experiment the author can run the creative comparisons without asking the requester to act as the editor. Follow the production precheck when the task is a production edit. Publication has its own authorization.

## Inspect the word clock

Store a private JSON plan with `fps`, `durationFrames` and contiguous half-open `shots`. A shot has `startFrame`, `endFrame`, `asset`, `emotion`, `inventory`, `script` and `words`. Each word has `text`, `startFrame`, `endFrame`, `actor` and `action`. Give each word its own onset frame. The runtime caption also takes a `line` number so it can accumulate a short readable group. Use the final narration's frame clock; if only provider offsets are available after retiming, label them estimates until playback or alignment verifies them.

```text
python scripts/audit_word_cues.py --plan word-plan.json --video candidate.mp4 --out word-review
```

Omit `--video` for a structural check during authoring. With a render, the tool compares the preceding frame with each of the first four frames of the word, stopping at the next cue or shot. The strongest change supplies the comparison tile so a one-frame impact remains visible in the audit. Use `--region LEFT TOP RIGHT BOTTOM` to focus on the actor, excluding captions if you are testing object motion. Inspect low-motion cues and the state changes shown on their before/after tiles. Joint movement, flicker and a moving camera may register as change. Compare the relevant native frames and audio before calling an action captured.

## Transfer the method to new subjects

Reuse camera, rig and cue plumbing. Choose actors and actions that explain the new story. For a keyboard, the word “press” could lower a keycap and move a linkage, “contact” could close the circuit and light a trace, and “release” could return the cap while preserving the closed/open state change. For an optical mouse, use a lit surface, sensor samples, a motion vector and cursor movement across successive words. Carry the same object through the relevant detail shots and verify the visible result before adding decoration.
