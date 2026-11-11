# Instagram Reel sound effects

**Created:** 2026-11-11
**Status:** In development
**Feature branch:** `raghu/instagram-reel-sfx`

## User scenarios

1. Download a public Instagram Reel into a private workspace while retaining its canonical URL, creator, metadata, and original media.
2. Cut named, time-bounded sound-effect candidates from the reel without changing the source or silently including a voice track.
3. Catalogue reviewed effect files in the private stock library with source provenance and an honest rights and voice-review state. Unknown rights or unreviewed voice block reuse.

## Requirements

- Create an independently discoverable `content-studio-video-reel-sfx` skill with repeatable download and lossless PCM extraction commands.
- Accept only canonical Instagram Reel URLs; strip tracking parameters; fail clearly if the public page needs login or is unavailable. Never bypass access controls.
- Record source hash and precise clip boundaries. Refuse out-of-range or empty cuts and preserve the downloaded original.
- Do not claim a mixed-track cut is voice-free based on a filter or automatic classifier. Require complete listening review of each candidate before marking it voice-free.
- Extend the existing private stock library with audio SFX, duration, source attribution, rights state, and a reuse gate. Never commit reel media or extracted audio.
- Run the approved Content Studio precheck before production extraction and catalogue import. Do not publish or place extracted effects in a video as part of this workflow.

## Acceptance

- A synthetic fixture demonstrates exact bounded WAV extraction, source preservation, and invalid-range rejection.
- Unknown-rights or voice-pending effects are catalogued as reference-only; confirmed eligible effects remain discoverable by kind and tags.
- Skill discovery, method matrix, documentation, and focused tests pass.
