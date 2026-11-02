// Back-compat shim. The house color tokens now live in `src/design/color.ts`
// (single source of truth). Shared shell components import from here; videos
// should import from the design system directly.
export * from '../design/color.ts';
