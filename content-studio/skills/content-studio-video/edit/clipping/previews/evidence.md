# Clipping delivery evidence

## Real multi-hero source

The source is the owned Out of Office Mode archive of `SeaWorld Dolphin Show | Amazing Dolphin Performance` (video ID `Fm6Wh4U_2Kw`), with source SHA-256 `52078a378b7014ba9fbc12e58e7ac8d31b4063673e37d023d5819b73bab8bb68`. It is an 11:54.874, 3840×2160, BT.709 video with stereo Opus audio. The approved selection is source seconds 540–546. Contact sheets locate the trainer and dolphins; a group box centers one stable 9:16 crop, while separate labelled boxes let the framing report check each annotated subject. The report measured minimum annotated coverage `1.0`, but those coarse boxes do not establish frame-by-frame semantic tracking.

The selected subjects crop is normalized `(x=0.341797, y=0, w=0.316406, h=1)`. Center cropping proposed the same window; saliency proposed `x=0.676167`, showing only water in its middle guide frame, so it was rejected. The crop removes 68.36% of the wide source context. Start, middle and end guides and a six-second animated preview were inspected before the exact timeline revision was approved.

The exact 360×640, 30 fps, six-second master has output SHA-256 `d176b983dbcbbd0beb2fc8677e20bb43420a5c5e9eb22c97d947170a75019668`, bound to approved timeline fingerprint `ea878a80ad574fc7529077c7c269e157fe809ef0580b82b92e52a8ec3c5b15e4`. The render record reports one video and one audio encode. `timeline.py verify` confirmed H.264 picture, AAC audio, BT.709 color, exact duration and hash; its final-render inspector found no black, frozen, flash, or audio-silence candidates. The delivered bytes matched the user-reviewed bounded preview hash. Measured output audio was −10.22 LUFS integrated with −0.34 dBTP true peak; no mastering was requested or applied. The GIFs have 36 time-aligned comparison frames and 48 portrait frames. They contain no audio.

The [source-versus-Reel GIF](real-source-vs-reel.gif) and [clipped GIF](real-clipped-reel.gif) were generated with [build_real_demo.py](build_real_demo.py). That script requires the exact full-render record and current selection/source hashes before writing README evidence; `--preview` is explicit for disposable review aids. The owned source and full MP4 are outside the Git bundle. Only the two requested, compact real-footage GIFs are committed.

## Synthetic regression evidence

`tests/test_clipping.py` creates a four-second 160×90 SDR source with a red hero on the right, a green distractor on the left, and four one-second audio tones. It selects source seconds 1–3, proposes a 9:16 hero crop from supplied boxes, emits pending timeline changes, and renders a 90×160 fixture through the existing delivery timeline.

The focused test checks that the exact output is two seconds, contains the red hero at a phone-sized sample point, carries an audio stream with the expected 440 Hz then 880 Hz source-time markers, and reports one video and one audio encode. `timeline.py verify` checks the delivered bytes, streams, dimensions, frame rate and duration and writes bounded frame evidence to the disposable test directory. The test also confirms source bytes remain unchanged and a changed selection blocks timeline validation.

In a separate synthetic proof run, the crop proposal image and exact delivered frame were opened at their native dimensions. The red hero remained visible against the blue field in both; the green distractor outside the approved crop was absent. The small fixture establishes geometry and source-to-output behavior only.

A second synthetic source moves the red hero from the right half to the left half at the crop boundary. The test proposes adjacent crops with different horizontal positions, renders them as one continuous source range, and checks the red hero at the center of both delivered intervals. A real crop jump still needs human motion review.

Run `python -m unittest discover -s content-studio/skills/content-studio-video/edit/clipping/tests -p "test_*.py"`. Generated source, preview, and master files live in a temporary directory and are never committed. For real footage, a human must still review the complete output and hero movement at phone size; the synthetic test does not establish creative quality.
