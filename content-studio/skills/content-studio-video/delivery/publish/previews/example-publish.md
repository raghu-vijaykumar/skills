# Publish preview example

Illustrative command/output example. Preview is not authorization.

```powershell
node content-studio/scripts/cli.mjs publish --channel <slug> --draft <id>
node content-studio/scripts/cli.mjs publish --channel <slug> --draft <id> --confirm
```

The preview validates the master, title, description, thumbnail, creative record, music
credits, and package hashes. `--confirm` is only for an explicit human publication
request. Scheduled/private uploads stay drafts until a public backup is verified.
