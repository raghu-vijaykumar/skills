# AI thumbnail workflow

Generate the thumbnail with an image-generation model. A raw video frame with
overlaid text is only a fallback when the user explicitly asks for it.

## Inputs

1. Capture 4-6 representative frames from `video.mp4` at different moments.
   Prefer frames that show the main subject, a clear action, and the setting.
2. Gather the spoken context: `transcript.json`, an authored voiceover, or the
   audio description. If `transcript.json` has `speech: false`, say that there
   is no spoken hook and use the ambient audio and visible subject instead.
3. Read `title.txt` and `description.txt`, or draft them from the same audio and
   visual context.

## Prompt template

```text
Create a YouTube thumbnail in 16:9 landscape at 1280x720.

Video context:
- Title: <title>
- Spoken/voiceover hook: <exact quote or "no speech; ambient audio only">
- Subjects: <subjects visible in the supplied frames>
- Setting: <setting visible in the supplied frames>
- Tone: <tone from the audio and footage>

Use the supplied frames as visual reference for the subject, setting, and color.
Create a polished editorial image, not a screenshot with a text box.
Include short thumbnail text: "<3-6 words>".
Keep the subject large and readable at small size. Leave safe margins.
Do not invent landmarks, brands, logos, locations, or events that are not in the
frames or the spoken context. Do not add watermarks.
```

## Approval

Show the generated image to the user. If they request changes, regenerate with
the corrected context or composition. Write `thumbnail.png` only after approval.
Keep the prompt, reference frames, and accepted image together for provenance.

## Requirements

- 16:9 landscape, 1280x720 or larger.
- Under 2 MB for YouTube.
- Text is short, legible, and truthful.
- No fake logos, no misleading claims, no unrelated people.
- If the video has no speech, do not claim a spoken hook in the thumbnail or
  metadata.
- The title and description must use the same transcript/voiceover/audio context
  as the thumbnail, not just the visuals.
