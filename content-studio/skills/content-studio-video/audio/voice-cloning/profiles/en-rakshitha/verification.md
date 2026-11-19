# en-rakshitha verification

Raghu confirmed Rakshitha's consent for English cloning from the supplied
recording and selected take 2 after listening to three local previews. Only
take 2 is in this profile. Its WAV is 6.75 seconds and has SHA-256
`bf0a148fc49df91a64bc57ef6f90f4e86c7d1f34b07ec5b916253fce3a1452ff`.

The selected direct Chatterbox Turbo preview was 7.30 seconds, 24 kHz mono,
with a peak of -6.2 dBFS. Local Whisper-small transcription recovered the
intended English test line. A real render through the installed Content Studio
`voice.py` route used `en-rakshitha`, `take2`, and the same seed. Its waveform
matched the selected preview within PCM rounding (maximum sample difference
`0.0000648`).

After copying the profile into the repository, `voice.py status` resolved the
bundled profile with only `take2` and no missing samples. A `synthesize
--dry-run` bound the expected reference SHA-256. The focused voice test suite
passed 52 tests; `npm run check:docs` and `npm run check:capabilities` passed.
The full source recording, other takes, generated previews, model weights,
and Python environment remain outside Git.

Each future script still requires its own exact-word and human listening
review before production use.
