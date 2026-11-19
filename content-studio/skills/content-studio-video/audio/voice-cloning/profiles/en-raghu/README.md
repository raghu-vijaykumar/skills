# en-raghu English voice profile

The speaker supplied one English recording, listened to clone previews made
from take 2 and take 3, liked both, and explicitly asked to add this profile to
Content Studio and commit and push it. Both references are preserved so a later
script can choose the delivery that fits its narration.

| Field | Value |
| --- | --- |
| Profile | `en-raghu` |
| Language | English (`en`) |
| Backend | Local Chatterbox Turbo |
| References | `take2` and `take3`, 9.7 s each |
| Model weights | External to Git; official revision recorded in `profile.json` |

Use `voice.py status --profile en-raghu` to inspect the profile. For a reviewed
English script, pass `--reference-variant take2` or `take3` to `voice.py
synthesize`. The full commands and optional environment setup are in
[Chatterbox Turbo guidance](../../references/chatterbox-turbo.md).

The WAV files contain biometric voice data. They are committed only because
the speaker explicitly requested this repository addition. Removing files in
a later commit would not erase them from Git history. Generated narration
still needs exact-word and human listening review before production use.
