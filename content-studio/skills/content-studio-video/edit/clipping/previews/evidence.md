# Synthetic delivery evidence

`tests/test_clipping.py` creates a four-second 160×90 SDR source with a red hero on the right, a green distractor on the left, and four one-second audio tones. It selects source seconds 1–3, proposes a 9:16 hero crop from supplied boxes, emits pending timeline changes, and renders a 90×160 fixture through the existing delivery timeline.

The focused test checks that the exact output is two seconds, contains the red hero at a phone-sized sample point, carries an audio stream with the expected 440 Hz then 880 Hz source-time markers, and reports one video and one audio encode. `timeline.py verify` checks the delivered bytes, streams, dimensions, frame rate and duration and writes bounded frame evidence to the disposable test directory. The test also confirms source bytes remain unchanged and a changed selection blocks timeline validation.

In a separate synthetic proof run, the crop proposal image and exact delivered frame were opened at their native dimensions. The red hero remained visible against the blue field in both; the green distractor outside the approved crop was absent. The small fixture establishes geometry and source-to-output behavior only.

A second synthetic source moves the red hero from the right half to the left half at the crop boundary. The test proposes adjacent crops with different horizontal positions, renders them as one continuous source range, and checks the red hero at the center of both delivered intervals. A real crop jump still needs human motion review.

Run `python -m unittest discover -s content-studio/skills/content-studio-video/edit/clipping/tests -p "test_*.py"`. Generated source, preview, and master files live in a temporary directory and are never committed. For real footage, a human must still review the complete output and hero movement at phone size; the synthetic test does not establish creative quality.
