# LinkedIn draft contract

The default workspace is `C:\workspace\content\linkedin-personal` on Windows; `CONTENT_STUDIO_LINKEDIN_WORKSPACE` or `--workspace` changes it. Draft IDs are lowercase slugs. The agent may resume from any chat by ID.

```powershell
content-studio linkedin new --draft my-idea --idea "My rough opinion"
content-studio linkedin list
content-studio linkedin status --draft my-idea
content-studio linkedin resume --draft my-idea
content-studio linkedin approve --draft my-idea --stage angle --note "User approved plan and angle"
content-studio linkedin approve --draft my-idea --stage draft --note "User approved copy and visual draft"
content-studio linkedin render-image --draft my-idea
content-studio linkedin build-carousel --draft my-idea
content-studio linkedin approve --draft my-idea --stage final --note "User reviewed exact package"
content-studio linkedin publish --draft my-idea
content-studio linkedin publish --draft my-idea --confirm --authorization-note "User explicitly asked to post this approved package"
```

`new` creates `idea.md`, `brief.json`, `sources.json`, `post.md`, `creative.json`, `linkedin-state.json` and `.content-studio/preflight/`. Before angle approval, fill the brief with `angle`, `stance`, `audience`, `format` (`text`, `image`, `animated-image`, `carousel`, `video`), `formatReason`, `brand` (a preset slug, including `personal` and `revise-labs`), `language`, and `narration` (`narrated` or `silent` for video). Project presets live at `<workspace>/presets/<brand>.json` with a `name` and optional full Remotion `theme`. The approved angle hashes the preset file; changing it requires renewed review. Per-post `creative.theme` and `creative.styleName` may override the preset for the bundled card renderer. `sources.json` has `claims` with `text`, `type` (`fact` or `opinion`), and a `sourceUrl` for every fact; its `assets` need `id`, `origin`, `rights`, and an optional local `path`.

`post.md` holds the exact plain-text LinkedIn copy; Markdown syntax is not converted by the publisher. For an image or animated image, `creative.json` needs `imageConcept`, `altText`, `mediaOrigin` (`original-illustration` or `evidence`) and either `assetMethod` or `evidenceId`. Animated images also need `motionPlan` and a 1080×1350 `animation.gif` with 2–250 frames. `render-image` additionally reads `card.heading`, optional `card.body`/`card.phase`, and optional `illustrationPath`; it writes `image.png`. An evidence card finds its source file from the matching asset's `path`. Original art is labelled as illustration on the card. A carousel needs `title`, `slideOutline` with one entry per page, and a portrait `carousel.pdf`; the optional `build-carousel` command assembles sorted 1080×1350 PNGs from `slides/`. On a personal organic post this is a LinkedIn document post, not the sponsored Carousel API. For a video, `creative.json` needs a `script`, nonempty `storyboard`, and `coverConcept`. An approved method may use the existing `videogen init` route and deliver `video.mp4`, `cover.png`, and `captions.srt` when narrated. The production plan must name the exact project, commands and outputs. Images and video covers are 1080×1350 PNG; video is 1080×1350 H.264 for 45–90 seconds with AAC audio when narrated.

The plan in `.content-studio/preflight/plan.json` must name selected methods, exact argv, benchmark basis, fallbacks and review criteria before angle approval. Step S04 needs `method_id`, `inputs`, and `fallback`; every media plan also needs a `command` argv array for its selected renderer. `approve` records the user's decision and checklist evidence. Approval hashes are checked again on resume and publish; editing upstream material or the selected preset requires reviewing the affected checkpoint again. `linkedin publish` stores a local dry-run fingerprint and shows exact copy and file hashes; `--confirm` refuses a package that has not been shown in a matching dry run.

## Personal account connection

Create a LinkedIn developer app with the **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect** products. Configure its redirect URI as `http://127.0.0.1:53621/callback` (or the chosen `--port`). Put `{ "clientId": "...", "clientSecret": "..." }` in the ignored `<workspace>/secrets/linkedin-client.json`, then run `content-studio linkedin connect`. Open the printed URL and authorize `openid profile w_member_social`. The token and member URN are stored in `<workspace>/secrets/linkedin-token.json`; expired tokens require reconnecting. The default REST header version is `202610`, overridable with `CONTENT_STUDIO_LINKEDIN_API_VERSION` after checking [LinkedIn's current versioning](https://learn.microsoft.com/en-us/linkedin/marketing/versioning).

LinkedIn's [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api) supports organic text, image, video and document posts. The [Images API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api), [Documents API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api) and [Videos API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api) require upload before post creation. API product access is an external prerequisite: an explicit 401/403 leaves the reviewed package intact. `linkedin-receipt.json` records a post attempt before the irreversible create request; an uncertain result blocks automatic retry.
