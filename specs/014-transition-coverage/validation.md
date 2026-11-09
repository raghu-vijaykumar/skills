# Transition coverage validation

## Bounded visual evidence

Two generated 640×360, 30 fps shots with distinct grids, colors, labels, and
440/660 Hz audio were joined with each of the eight new methods. Each used a
0.8-second overlap. All eight outputs decoded with a 2.2-second resolved
duration and audio crossfade; neither source file changed. Frames at 0.65,
0.90, 1.10, 1.30, and 1.55 seconds were combined into a contact sheet and
visually inspected. The panel, fold, vertical fluid edge, expanding pools,
warm rising edge, shrinking picture, rotating picture, and heart reveal were
distinct. These are review candidates, not approval of a future production
timeline. The generated clips and contact sheet remain outside Git.

## Bounded performance comparison

On this machine, the same 2.2-second output at 1920×1080 took 1.40 seconds
with a native cross-fade, 25.78 seconds with the custom heart, and 20.04
seconds with the custom spin. These figures are not a 4K estimate; production
plans should benchmark their chosen custom effect at the intended resolution.

## Automated checks

- Specialist transition suite: 32 tests passed, including all eight custom
  joins decoded with audio and unchanged sources.
- Delivery timeline suite: 30 tests passed. All 26 join and six point adapters
  made short actual outputs; a mixed custom join plus point effect produced one
  approved export and passed exact-output verification.
- `npm run check:docs` passed after documentation updates.
- The staged diff contained only transition feature files and passed
  `git diff --cached --check`.

## Remaining review boundary

These treatments are intentionally labelled approximations. Each use on a
real edit still needs the mandatory Content Studio plan, exact timeline
approval, a bounded preview, and review of the final output. The code change
does not alter any existing video or timeline revision.
