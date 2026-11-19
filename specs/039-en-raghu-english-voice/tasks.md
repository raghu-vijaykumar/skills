# Tasks: en-raghu English Voice

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Implementation

- [x] T001 Bundle the two approved reference takes with consent, hashes, and usage notes under `profiles/en-raghu/`.
- [x] T002 Add the optional Chatterbox Turbo loader and synthesis adapter in `scripts/chatterbox_backend.py`.
- [x] T003 Route `voice.py synthesize` by profile backend and select named English references without changing IndicF5 calls.
- [x] T004 Add unit tests for reference choice, missing or modified files, backend routing, and model directory validation.
- [x] T005 Update `SKILL.md`, `README.md`, `methods.json`, and `references/chatterbox-turbo.md` with the English command and review gates.
- [x] T006 Run focused and documentation checks and render one real English test segment for word, clipping, and format verification.
- [x] T007 Review the staged diff and verify generated media and model weights are excluded. Commit and push follow the repository's feature-completion rule.
