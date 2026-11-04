---
name: content-studio-voice
description: Register a consented personal voice profile for future narration, then synthesize approved voiceover scripts with a locally configured backend.
---
# Content Studio Voice
Voice samples will be supplied later. Until then, voice cloning is **not configured** and must never silently fall back to another person's voice. Register only a voice the user owns or is explicitly authorized to clone, with recorded consent. Keep samples and model weights outside Git and do not commit them.

Profile configuration lives in the local content workspace (e.g. `.content-studio/voice/profile.json`) and references local sample paths, language, backend, consent record and quality checks. A backend adapter (e.g. an installed, license-reviewed XTTS-compatible or F5-TTS-compatible runtime) must be explicitly configured; this skill does not claim an installed synthesis model. Only synthesize a **human-approved** narration script, with matching source-video hash. Preserve the original dialogue where the prompt says to use it. Export a voiceover WAV and a timing manifest, then request a listening review for pronunciation, Kannada-English code-switching, pacing and identity fidelity. Do not publish cloned speech without human review. Do not clone a third party without permission.
