# Meme catalogue example

Illustrative catalogue operations. No third-party media is committed.

```powershell
python content-studio/skills/content-studio-video/memes/scripts/memes.py --library "D:/ContentStudio/memes" init
python content-studio/skills/content-studio-video/memes/scripts/memes.py --library "D:/ContentStudio/memes" add --file "<approved-reaction>" --name "Synthetic reaction" --tags "surprise,travel" --language en --license "owned" --source "synthetic"
python content-studio/skills/content-studio-video/memes/scripts/memes.py --library "D:/ContentStudio/memes" search --query surprise
```

Imports are SHA-256 deduplicated and preserve the source. Items with unknown rights are
not eligible for publishing suggestions.
