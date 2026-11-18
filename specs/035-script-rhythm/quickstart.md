# Quickstart validation

From the repository root:

```powershell
python -m unittest discover -s content-studio/skills/content-studio-video/review/understand/tests -p "test_*.py"
node --test content-studio/skills/content-studio-video/animation/videogen/tests/script-rhythm.test.mjs
npm run check:docs
```

For a code-driven draft, run `node content-studio/skills/content-studio-video/animation/videogen/narration-timing/scripts/narration.mjs <draft-folder> --rhythm-only` and inspect `assets/generated/audio/narration-rhythm.json`. No synthesis or render is started.
