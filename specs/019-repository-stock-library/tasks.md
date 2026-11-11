# Tasks: Repository stock library

## Copy and protect assets

- [x] T001 Copy catalogue and all seven media files into the stock skill's `assets/` folder; verify SHA-256.
- [x] T002 Copy old production review evidence to the task visualization folder; verify every file.
- [x] T003 Add a narrow ignore for local-only SFX WAVs and review evidence.

## Update the skill

- [x] T004 Allow the canonical repository library in `scripts/library.py` and update focused tests.
- [x] T005 Update stock, Reel, and top-level documentation for the canonical location.
- [x] T006 Exclude local-only WAVs and review evidence from managed installs.

## Verify and finish

- [ ] T007 Run tests, documentation checks, Git ignore and LFS checks, and asset hash verification.
- [ ] T008 Stage relevant tracked files, review the staged diff, commit, push, and verify the remote.
- [ ] T009 After verifying the new location, remove only the old stock-library folder.
