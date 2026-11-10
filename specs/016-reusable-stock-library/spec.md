# Reusable Content Studio stock library

**Created:** 2026-11-10
**Status:** Skill implementation complete; full 4K asset production requires approval of the separate Content Studio precheck plan

## User scenarios

1. Select a reusable Like / Share / Subscribe animation by named visual variant for any video, then render it at the target frame size and placement.
2. Import a self-created meme, GIF, sticker, or stock clip into a private local library and find it later by name, type, or tag.
3. Browse the stock skill README for built-in designs and the private library README for actual imported media. Keep the existing meme catalogue's contextual insertion workflow available.

## Requirements

- Create an independently callable `content-studio-video-stock-library` subskill with one canonical CTA generator and a catalogue of selectable variants.
- Preserve the existing CTA's default visual output and old command path. Add at least two visibly distinct variants with the same Like, Share, Subscribe-to-Subscribed, bell, and exit sequence.
- Generate transparent, silent alpha footage at the requested resolution, frame rate, duration, and position. Default reuse target is 3840×2160, 30 fps.
- Provide a local-only importer for user-created media. Deduplicate by SHA-256; preserve originals; copy private media outside Git; record authorship/rights, tags, and type; update the private library's `README.md` catalogue.
- Keep the repository's stock `README.md` as the catalogue of built-in reusable designs. Cross-link the corresponding motion graphics and memes READMEs without claiming unrendered media exists.
- Require the Content Studio precheck and human approval before full stock production renders or insertion into a video. Existing approved video/media remain unchanged.
- Add focused tests, docs, and rendered comparison evidence. Do not commit generated media.

## Acceptance

- Named variants yield distinct nonempty RGBA frames with transparent background and correct state timing.
- The old CLI still invokes the canonical implementation and retains its default behavior.
- Imported media is copied and deduplicated; private README lists real assets only; unsupported formats and a library inside the source repo are rejected.
- Documentation and focused tests pass. A full variant production render awaits its own approved precheck plan.
