# Voice synthesis example

No voice audio is committed: enrolled profiles are biometric and workspace profiles are
kept outside Git. This is a labelled command/output example.

```powershell
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> enroll --profile my-voice --samples <sample1.wav> <sample2.wav> --language kn-en --consent --consent-note "<explicit consent>"
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> synthesize --profile my-voice --script narration.json --model-dir <IndicF5> --reference <reference.wav> --reference-text "<exact transcript>" --nfe-step 32
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> assemble --script narration.json --video <master.mp4> --preview
```

Outputs stay under `<workspace>/.content-studio/voice/`. Round-trip transcribe and
listen before approval; synthetic speech is disclosed where appropriate.
