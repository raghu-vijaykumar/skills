---
name: content-studio-styles
description: List built-in and project-enabled Content Studio styles with their formats and use cases. Use when choosing or checking a video, carousel, or post treatment.
---

# Content Studio Styles

Run `node <this-skill>/scripts/list.mjs` to list the built-in styles available in the installed bundle. The script reads the runtime registry; `--json` gives structured output. Run `--themes` separately to list built-in channel identities. A theme supplies brand, color, and typography; a style supplies the editorial treatment and supported formats.

For a specific videogen project, run `npx --no-install videogen styles` from its root and read `videogen.config.ts`. Show which built-in styles are enabled by that project and include any custom styles registered in its config. A project may enable only part of the built-in catalog. If it has not installed its pinned package yet, use that project's normal install workflow before listing its enabled styles.

Present the result as style ID, name, use, formats, and whether it is enabled in the selected project. Note that Evidence Lab requires firsthand evidence, Rapid Take is the video-only satirical news style, Hairline is a video-only line-art animation style, and Tech Dispatch is carousel/post only. Read [themes and styles](../content-studio-videogen/references/themes.md) for registration, [Rapid Take](../content-studio-videogen/references/rapid-take.md) for the satirical video treatment, and [Hairline](../content-studio-videogen/references/hairline.md) when that style is being considered. Record a chosen theme and style in the draft's creative metadata; listing styles does not change shared presets.
