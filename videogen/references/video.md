# Video workflow

Start a new draft with `videogen scaffold <id> --title "Working title"`. It creates a per-video Remotion entry, metadata and title scene without replacing an existing idea brief.

The project `videogen.config.ts` names the Remotion entry point and video directory. It may provide `entryPointForVideo(id)` so each draft bundles alone. Each `<videosDir>/<id>/content/video.yaml` declares `video.compositionId`; music-only work also declares `video.durationSeconds`. Remotion is authoritative for width, height, frame rate, and duration.

For narrated work, keep narration YAML as authored text and generated cue audio as timing. Show the actual mechanism and label illustrative values. Start with a small pilot or hero shot, inspect it alone, then inspect it in the narrated edit. Prefer semantic state changes and camera detail shots over generic boxes and arrows. Build a storyboard with teaching point, protagonist, causal visual event, primary motion, framing, transition, and payoff. The content repository owns that storyboard and its review record.

Run `videogen narration <id>` when narration is new or changed, then `videogen check <id>`. The check verifies the source hash, cue list, and audio duration. Existing version 3 narration caches are accepted only when their original source is unchanged and they use no later rate or pause features; this preserves approved legacy timing. Inspect Studio playback and frames at the hook, introductions, important state changes, failure or recovery, and ending. Use short `videogen render <id> --from S --to E` only where motion needs extra evidence. Fix source layout and motion rather than suppressing gates. Record timecoded observations and recheck after changes. Reserve `videogen render <id> --delivery` for an explicitly requested delivery render.

Project-specific checks are registered in `videogen.config.ts` and run with the package check. They may cover layout, camera clearance, motion, font sizes, media provenance, and creative-review evidence. Do not downgrade a failed check to complete a video.
