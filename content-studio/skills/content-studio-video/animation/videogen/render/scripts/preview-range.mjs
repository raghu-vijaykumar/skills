// Separate operation entrypoint; the videogen CLI remains the maintained backend.
// A preview must stay bounded even when this skill is called directly.
if (!process.argv.includes('--from') || !process.argv.includes('--to') || process.argv.includes('--delivery')) {
  throw new Error('preview-range requires --from and --to and cannot use --delivery');
}
process.argv.splice(2, 0, 'render');
await import('../../scripts/cli.mjs');
