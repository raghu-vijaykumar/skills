# en-rakshitha English voice profile

Rakshitha consented to English voice cloning from `Recording (3).m4a`, as
confirmed by Raghu. Three local Chatterbox Turbo previews were generated, and
Raghu selected take 2 after listening. The repository profile contains only
that 6.75-second reference. The full recording, other takes, generated
previews, model weights, and Python environment remain in private local
storage.

| Field | Value |
| --- | --- |
| Profile | `en-rakshitha` |
| Language | English (`en`) |
| Backend | Local Chatterbox Turbo |
| Reference | `take2`, 6.75 seconds |
| Model revision | Pinned in `profile.json` |

Use `voice.py status --profile en-rakshitha` to inspect the bundled profile.
For a reviewed English script, pass `--profile en-rakshitha` and
`--reference-variant take2` to `voice.py synthesize`. See the
[Chatterbox Turbo guidance](../../references/chatterbox-turbo.md) for the full
command and local model setup.

The reference WAV is biometric voice data. Removing it in a later commit
would not erase the earlier Git history. Each generated script still needs
word accuracy and human listening review before production use.
The [verification record](verification.md) summarizes the local preview and
bundled-profile checks.
