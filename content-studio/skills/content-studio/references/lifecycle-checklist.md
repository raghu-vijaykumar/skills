# Lifecycle checklist

The main `content-studio` router owns one deterministic checklist per draft:
`draft/lifecycle-checklist.json`. It is created before production work and is
updated at every stage.

Direct use of a specialist skill is a one-off action. It does not create this
checklist and is not blocked by it. When the router is used, the checklist is
mandatory.

## Rule

Every item must end as one of:

| Status | Meaning | Required |
|---|---|---|
| `done` | Completed and reviewed | `evidence` or `note` |
| `not_applicable` | Does not apply to this draft | `reason` |
| `deferred` | Postponed | `reason`; blocks pre-publish verification |

`pending` always blocks. A `deferred` pre-publish item blocks approval. Post-publish
items start deferred and must become `done` or `not_applicable` before the draft is
closed.

## Items

| ID | Phase | Applies | Item | Done when |
|---|---|---|---|---|
| C01 | pre-publish | all | Channel and draft rules reviewed | Channel owner rules, current draft, and existing approvals read |
| C02 | pre-publish | all | Production kind recorded | Draft is explicitly `edited` or `remotion`, and `draft.json` agrees |
| C03 | pre-publish | all | Idea brief or story outline approved | Approved brief/outline, or justified not applicable for a supplied edit |
| C04 | pre-publish | edited | Camera clips preprocessed | Duplicates quarantined, ordered, blur/DV gates reviewed, clean exports available |
| C05 | pre-publish | edited | AutoCut rough cut reviewed | Human reviewed the rough cut and review media, including reframe previews when used; target orientation/fit recorded, or AutoCut explicitly deferred |
| C06 | pre-publish | all | Audio mastered and reviewed | Loudness/dynamics checked; not applicable only when no audio treatment is needed |
| C07 | pre-publish | all | Master edit or render complete | Full-length master exists and was watched end to end |
| C08 | pre-publish | all | Color, HDR, and Dolby Vision reviewed | SDR tags/tone mapping checked; DV proof reviewed when applicable |
| C09 | pre-publish | edited | Transcript reviewed | `transcript.json` matches the master hash and spoken content, or records `speech: false` |
| C10 | pre-publish | edited | Captions reviewed | `captions.srt` timing/text reviewed, or captions explicitly declined (including a `speech: false` transcript) |
| C11 | pre-publish | all | Thumbnail approved | AI-generated 16:9 thumbnail from representative frames plus audio/voiceover context; approved |
| C12 | pre-publish | all | Music selected, mixed, and licensed | `music-selection.json`, `music-credits.txt`, and a reviewed music-mixed master, or explicitly no music |
| C13 | pre-publish | all | Title and description reviewed | Exact copy derived from transcript/voiceover/audio context, including required music attribution |
| C14 | pre-publish | all | Rights, licenses, and consent reviewed | Footage, music, fonts, logos, faces, locations, and client data cleared |
| C15 | pre-publish | all | Creative metadata recorded | `creative.json` has themeId, styleId, format, renderer, choices |
| C16 | pre-publish | all | Package approval recorded | `package-approval.json` matches current publication files |
| C17 | pre-publish | all | Publish plan previewed | Platform, visibility, schedule, copy, thumbnail, captions previewed |
| C18 | post-publish | all | Published or scheduled with receipt | Platform ID and receipt recorded; uncertain results reconciled |
| C19 | post-publish | all | Public or scheduled status verified | Live/scheduled state matches intended visibility and schedule |
| C20 | post-publish | all | Public YouTube backup completed | Video, exact metadata, thumbnail, and publish receipt backed up |
| C21 | post-publish | all | Drive sync verified | `rclone check` evidence confirms the durable media copy |
| C22 | post-publish | all | Draft handoff or close recorded | Draft moved/closed under channel policy; source retained |

Do not renumber existing IDs. Add new items at the end with the next ID.

## Commands

Initialize or resume the checklist:

```powershell
python <this-skill>/scripts/checklist.py `
  --channel <slug> --draft <id> --kind edited init
```

Use `--kind remotion` for code-driven videos. `init` also marks `draft.json`
with `"lifecycle": "main"`, which makes package approval require the checklist.
It is idempotent; `--force` resets every status and should be rare.

Mark an item:

```powershell
python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> `
  set --id C07 --status done --evidence "video.mp4" --note "watched end to end"

python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> `
  set --id C10 --status not_applicable --reason "captions not published for this draft"

python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> `
  set --id C18 --status deferred --reason "post-publish gate"
```

Show or verify:

```powershell
python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> status
python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> verify --phase pre_publish
python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> verify --phase all
```

`verify` exits 1 and lists every uncovered item. At approval and confirmed
publishing, the package gate independently rejects any main-lifecycle draft whose
pre-publish items are pending, deferred, done without evidence, or not applicable
without a reason.

## Defaults

- Post-publish items C18-C22 start `deferred` with the reason `post-publish gate`.
- For a Remotion draft, C04, C05, C09, and C10 start `not_applicable` with the
  reason `Remotion production has no camera footage`.
- Everything else starts `pending` and must be explicitly resolved.

## One-off use

If the user invokes `content-studio-videoedit`, `content-studio-audio`,
`content-studio-autocut`, or another specialist directly, do not create this
checklist. The specialist's own checks and review gates still apply.
