# Validation guide

1. Run the focused preflight tests with a synthetic mixed-format source; confirm all streams, observed timing, capability states, and original hash.
2. Render controlled defect and clean fixtures through the timeline; run exact-master inspection and compare timecoded findings to fixture truth.
3. Supply two caption cues, review a bounded portrait preview, approve the revised timeline, render, and inspect exact cue frames and output hash.
4. Analyze delayed/drifting camera and mic fixtures; listen to the bounded audition and verify report confidence and original hashes.
5. Generate a hero-led crop proposal with subject boxes and adjacent crop intervals; inspect coverage and guides at phone size.
6. Render a voice-plus-music loudness fixture; inspect analysis values, final LUFS/dBTP, and one audio encoder invocation.
7. Compare smart cut with accurate rendering on a long-GOP fixture and verify packet/frame/audio boundaries; confirm unsupported sources fail closed.
8. Preview and render speed, freeze, reverse, and loop timelines; verify output duration, frame order, audio treatment, and downstream cue timing.
9. Run `npm run check:docs` and relevant existing test suites. Review staged files before each coherent commit, push `main`, and verify `origin/main` matches the intended commits.
