# SFX workflow and cue contract

The pinned build source is Earshot commit `4ac3d2ac2b151e1c23376f9ce7f3047a17050013`. Clone it outside this repository when regenerating or making new sounds. `sfx.py` checks the exact commit. The shipped WAVs and catalogue work without Earshot installed.

```powershell
python content-studio/skills/content-studio-video/audio/sfx/scripts/sfx.py import-bank --earshot-root <earshot-checkout>
python content-studio/skills/content-studio-video/audio/sfx/scripts/sfx.py forge --earshot-root <earshot-checkout> --output <private-candidates-dir> -- <earshot-forge-options>
python content-studio/skills/content-studio-video/audio/sfx/scripts/sfx.py fit --earshot-root <earshot-checkout> --output <private-recipe.py> -- <source-recording> --report
python content-studio/skills/content-studio-video/audio/sfx/scripts/sfx.py adopt --earshot-root <earshot-checkout> --file <selected.wav> --recipe <recipe.py> --mode forge --creator <name> --rights owned --redistributable
python content-studio/skills/content-studio-video/audio/sfx/scripts/sfx.py review --sound-id <earshot-id> --note "Listened to the whole effect and tail; confirmed label"
```

Use `fit` only with an owned or properly licensed source recording. For a fitted candidate, provide `--mode fit --source-recording <file> --source-license <terms>` to `adopt`. Omit `--redistributable` if the source license does not permit shipping a standalone WAV or derived recipe. The generated candidate and its side-by-side report are review material, not an automatic catalogue approval. Installing Earshot's optional forge/fit dependencies is required for creation; the bank importer needs only NumPy and SciPy.
Created WAVs under `media/sfx/earshot/created/` are ignored by default. After the recording license and listening review are documented, explicitly force-add only the approved redistributable WAV and its recipe to Git.

After the target video's approved precheck, generate evidence:

```powershell
python content-studio/skills/content-studio-video/audio/sfx/scripts/events.py analyze-edited --video <supplied-edit.mp4> --evidence-dir <draft>/.content-studio/understanding/sfx-frames --output <draft>/.content-studio/understanding/sfx-events.json
python content-studio/skills/content-studio-video/audio/sfx/scripts/events.py analyze-remotion --plan <project>/scene-plan.json --output <project>/sfx-events.json
python content-studio/skills/content-studio-video/audio/sfx/scripts/events.py propose --events <sfx-events.json> --style calm --mode preview --music-bed <music-bed.wav> --output <sfx-proposal.json>
```

The event manifest is version 1, bound to the video or plan SHA-256. Each event has `id`, `time`, `event_type`, `confidence`, `audio_context`, and `evidence`. Edited cut and motion-peak bursts are deliberately low-confidence until a visual reviewer identifies the action from the actual frames and audio. Supported contexts are `quiet`, `music`, `narration`, `dialogue`, `natural`, and `unknown`; the last three do not get automatic effects. A proposal contains either `decision: candidate` with the asset hash, cue start, sync anchor, gain, and pending review, or `decision: no-effect` with its reason. For music-context events, provide the separate music bed; the selector measures 50 ms windows in the second before the cue and sets a capped level near 6 dB above that bed. Without the bed, it proposes no effect. Preview mode can suggest audited but unreviewed bank sounds; delivery mode requires sound approval.

Export the reviewed proposal as a timeline `changes.json` or Remotion `MediaClip` JSON with `export-timeline` or `export-remotion`. The timeline tool creates the immutable successor and bounded preview. For Remotion, pass the video folder as `--project`, the configured shared public folder as `--public-dir`, and the video folder's `content/sfx-cues.json` as `--output`; export requires a canonical `entry.tsx` and automatically mounts the cues through `MediaLayer` there. The SFX validator checks this entry. Render a bounded picture-and-sound range, then record `content/sfx-approval.json` with `actor: human`, `reviewer`, `review_note`, `approved_at`, and `cues_sha256` of the final cues file. Set each reviewed clip's `sound_review_required` to false only after its catalogue listening approval; set `review_status: approved` on the final cues JSON. The delivery gate rejects stale approvals or changed WAVs. An exported cue remains pending until the editor approves its exact timing, level, and picture/audio fit. For HDR/Dolby Vision supplied edits, initialize the delivery timeline with `--preserve-picture`; only uncut picture and audio-only changes qualify. Its final render checks packet identity and metadata before moving the output into place.
