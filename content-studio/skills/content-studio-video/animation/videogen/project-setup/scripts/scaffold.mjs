// Separate operation entrypoint; the videogen CLI remains the maintained backend.
process.argv.splice(2, 0, 'scaffold');
await import('../../scripts/cli.mjs');