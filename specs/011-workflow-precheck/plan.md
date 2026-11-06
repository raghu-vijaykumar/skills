# Implementation plan

## Technical context

Use the existing Python workflow runner and a Python precheck CLI in the same skill. Store per-draft JSON under `.content-studio/preflight/`. Add a small Node validator at the existing package approval boundary. No new dependencies or remote services are needed.

## Constitution check

- One canonical implementation: the workflow skill owns precheck; the package gate only validates its artifacts.
- Real validation: bounded benchmarks and tests cover current revision and checklist evidence.
- Portable interfaces: accept a draft path and optional sample path; no channel-specific assumptions.
- Reproducible release: source and docs enter the bundle; generated plans and media stay in draft workspaces.

## Design

`profile` captures machine and optional video metadata, then runs at most two seconds each of decode and Lanczos scaling. `init` creates an editable plan with sensible steps. `review` displays it. `approve` records the plan file's SHA-256 and creates the checklist. `set` records evidence for each step. `verify start` checks approval; `verify complete` checks all steps. The workflow runner requires a matching `plan_step` on every command and completed prior checklist steps. Package approval independently checks completion.

## Validation

Run focused Python and Node tests, docs check, and a synthetic bounded sample benchmark. Review the staged diff before commit.
