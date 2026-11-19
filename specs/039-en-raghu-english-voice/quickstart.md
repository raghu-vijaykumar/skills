# Quickstart: en-raghu English Voice

After installing the optional English backend and obtaining the official model files outside Git:

```powershell
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> status --profile en-raghu
python content-studio/skills/content-studio-video/audio/voice-cloning/scripts/voice.py --workspace <draft> synthesize --profile en-raghu --script <approved-script.json> --model-dir <local-chatterbox-turbo-checkpoint> --reference-variant take2 --device cpu
```

Use `--reference-variant take3` for the other approved reference. Review generated words and voice before assembling or publishing a production video.
