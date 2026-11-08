// Separate operation entrypoint; the videogen CLI remains the maintained backend.
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  throw new Error('init requires a new project directory; see the project-setup skill');
}
process.argv.splice(2, 0, 'init');
await import('../../scripts/cli.mjs');
