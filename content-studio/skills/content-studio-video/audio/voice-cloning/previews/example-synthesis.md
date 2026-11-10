# Voice synthesis example

## Actual bounded sample — review failed

[Listen to the IndicF5 output](indicf5-synthetic-demo.mp3) (3.43 s). This is
actual inference from the released IndicF5 checkpoint with a synthetic
Microsoft Zira Desktop reference, not a human voice. The requested line was
“Hello from Content Studio. This is a synthetic voice demo.” A local
Whisper tiny.en round trip heard “If pre-end goes on, let me make the real tune
in.” The recognizer transcribed the clean reference correctly, so this sample
does **not** pass the skill's text gate and must not be used as approved
narration. It demonstrates that the loader and synthesis route execute, not
that English cloning quality is acceptable.

The reference, temporary workspace, weights, and vocoder are kept outside Git.
The command below is a reproducible route with local paths substituted:

```powershell
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> enroll --profile my-voice --samples <sample1.wav> <sample2.wav> --language kn-en --consent --consent-note "<explicit consent>"
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> synthesize --profile my-voice --script narration.json --model-dir <IndicF5> --reference <reference.wav> --reference-text "<exact transcript>" --nfe-step 32
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> assemble --script narration.json --video <master.mp4> --preview
```

The gallery used `--device cuda` and a local Vocos directory through
`CONTENT_STUDIO_VOCODER_DIR`; the generated mono WAV is 24 kHz and was encoded
to this MP3 without changing its timing. Outputs stay under
`<workspace>/.content-studio/voice/`. Round-trip transcribe and listen before
approval; synthetic speech is disclosed where appropriate. The repository
already contains explicitly consented bundled human profiles; no new one was
used for this gallery run.
