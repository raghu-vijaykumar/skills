# Scene-authoring example

Illustrative scene specification, not a render. Scenes are authored in the project
with the shared `../runtime/` components.

```json
{
  "beat": "explain one mechanism",
  "hero": "one labelled mechanism",
  "narration": "Synthetic narration cue",
  "review": ["hero frame", "detail range", "narrated scene"]
}
```

Choose a clear representation for each beat, frame a hero element alone, and inspect a
detail shot before the full narrated scene. Do not claim a new renderer or asset exists
without checking the project runtime.
