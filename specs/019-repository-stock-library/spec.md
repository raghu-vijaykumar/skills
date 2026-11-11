# Feature Specification: Repository stock library

**Created**: 2026-11-11
**Branch**: `raghu/instagram-reel-sfx`
**Status**: In progress

## User stories

### US1 — Find assets in Content Studio (P1)

The seven catalogued stock assets move from `C:\workspace\content\stock-library` to the Content Studio stock-library skill's `assets/` folder. The catalogue keeps its existing IDs, descriptions, provenance, rights, and hashes. Owned CTA clips and catalogue metadata are tracked in Git.

### US2 — Keep Reel audio local (P1)

Because the public Git repository does not have confirmed redistribution rights for the four Reel excerpts, those WAVs remain in the skill's `assets/media/sfx/` folder on this machine but are ignored by Git and omitted from managed releases. Their catalogue entries remain `reference-only`. The source Reel itself stays outside Git.

### US3 — Empty the mistaken content location (P1)

After SHA-256 verification of all copied files and preservation of prior production review evidence outside Git, remove only the old `C:\workspace\content\stock-library` folder. No other Content Studio draft or content folder is changed.

## Acceptance

- Seven media files and catalogue metadata are available under the stock skill and retain their SHA-256 hashes.
- `git check-ignore` confirms the four WAVs are ignored; the CTA clips are Git LFS tracked; no source Reel or generated review evidence is staged.
- CLI, documentation, and tests use the repository stock location; a clean managed install omits local-only WAVs.
- The old stock-library folder is removed only after copy and Git verification.
