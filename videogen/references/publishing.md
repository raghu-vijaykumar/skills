# Publishing a finished video

Use this workflow only for an explicitly requested upload or schedule. `videogen publish` defaults to a dry run. Review the complete encoded master and run `videogen check <id>` before `--confirm`; the CLI repeats project checks for confirmed actions. Commit authored source and publishing metadata before upload. Keep generated MP4s and credentials out of Git.

| Action | Command |
|---|---|
| YouTube now | `videogen publish <id> --confirm` |
| Instagram Reel now | `videogen publish <id> --platform instagram --confirm` |
| YouTube native schedule | `videogen publish <id> --at 2026-12-01T18:00:00+05:30 --confirm` |

Run each without `--confirm` first to see the selected full-length render and metadata. Scheduling requires a future ISO timestamp with a timezone; Instagram is immediate only. There is no local publishing queue or background runner. A dry run needs no credentials and writes nothing.

## YouTube

The draft needs `publishing.youtube` metadata in `content/video.yaml`, matching `title.txt` and `description.txt`, and `thumbnail.png` or `thumbnail.jpg` at 2 MB or less. The project config can set `publish.youtube.clientFile`, `tokenFile`, and `categoryId`; alternatively set `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, and `YT_REFRESH_TOKEN`. YouTube scheduling sets `status.privacyStatus=private` and `status.publishAt` during upload. The returned ID is written to `draft.json` before thumbnail/playlist steps. If setup fails after upload, use `--resume`; an existing ID blocks a second upload.

## Instagram

The draft needs `publishing.instagram.caption`. Use a reviewed portrait 9:16 master, 3 seconds to 15 minutes at 23–60 fps. The skill makes a 1080×1920 H.264/AAC upload copy under the project's ignored `workDir`; the authored master is untouched. `ffmpeg` and `ffprobe` must be available for a confirmed upload. Set `publish.instagram.tokenFile` to an ignored JSON file containing `{ "accessToken": "...", "igUserId": "..." }`, or use `IG_ACCESS_TOKEN` and `IG_USER_ID`. `apiVersion` is optional.

The direct Meta upload creates a Reel container, sends the file to its returned upload URI, polls until `FINISHED`, then publishes. Its container ID and render/caption fingerprints are checkpointed in `draft.json`. Use `--resume` only for a container that has not attempted `media_publish`. If a publish call might have succeeded but returned no ID, inspect the Instagram account and reconcile the receipt before any retry. The CLI will refuse a second publish automatically. Commit the resulting receipt after success.

A public YouTube backup remains the content repository's handoff point: keep scheduled/private sources in drafts until content-helper verifies the public copy and Drive backup.
