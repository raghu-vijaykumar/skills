# Content-derived title and description

Vlog metadata must come from the actual master, not a template.

## Procedure

1. Sample 4–6 frames across the master, including the opening seconds, the main subject, any readable sign or landmark, and the ending. Use `content.py media frames --draft <id> --at 0:00,0:20,0:45,1:10,1:40` or an equivalent frame extraction.
2. Inspect the frames visually. Read visible signs, exhibit names, locations, activities, and species only when they are legible. Do not guess a species or place from a blurry frame.
3. Use supplied narration, voiceover, or transcript context when it exists. For a silent vlog, use the ambient audio and visual evidence and say that there is no narration.
4. Write `title.txt` as one specific line, at most 100 characters. Lead with the concrete subject or location, not with words like "test", "draft", "clip compilation", or "video".
5. Write `description.txt` as a short factual summary of what is shown, followed by relevant hashtags. Include music or location attribution when required. Do not claim events, speech, or places the footage does not support.
6. If the footage is too ambiguous to name, ask the user for the location or subject instead of inventing one.

## Reject static placeholders

These are not acceptable final metadata:

- `Skilltest — 6 Clip Test Edit`
- `A short test edit assembled from six camera clips...`
- any title that only describes the production process

A test run may keep a test folder name, but the published title and description still describe the content.

## Checklist link

This evidence satisfies C13 when the title and description are derived from sampled frames or supplied context. Keep the sampled contact sheet or frame paths as evidence.
