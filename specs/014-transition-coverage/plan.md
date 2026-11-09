# Implementation Plan: Complete transition coverage

**Branch**: `main`
**Spec**: [spec.md](spec.md)

## Design

1. Keep specialist catalog IDs, duration limits, and native mappings as the public transition vocabulary.
2. Add the specialist point and join effects missing from the delivery timeline. Preserve the existing point range and clip-overlap model.
3. Add eight named custom join expressions using two video inputs. Keep the expression recipes in shared source so the specialist and timeline use identical visuals. Normalize custom joins to a common pixel format and return to SDR delivery format before encoding.
4. Include the shared recipes and catalog bytes in the timeline renderer capability hash. Keep timeline approval immutable and reject stale approvals.
5. Use generated two-shot media with different colors/patterns and audio to render each effect at a bounded size. Inspect entrance, midpoint, and exit contact sheets, then run the existing timeline and transition suites plus docs validation.

## Risks and checks

- Complex custom expressions can be slow at 4K: bound the transition duration and compare pilot encode time against simple joins.
- Approximate effects can look alike: inspect real output frames and revise formulas that lack distinct motion.
- Coordinate remaps can damage color planes: use a common full-resolution planar format for custom joins, then convert once for delivery.
- Renderer changes invalidate existing timeline approvals by design; never use an old approval after this release.
