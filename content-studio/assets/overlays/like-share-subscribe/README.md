# Like / Share / Subscribe reusable overlay

Editable Remotion 4-second, 30fps composition. Built using vector icons and React animations; no external assets. Overlay is transparent in the composition (no background layer). Source is suitable for 16:9; change composition dimensions and bottom/scale for Shorts.

## Render

From a project with `remotion`, `@remotion/cli`, React, and TypeScript installed, use:

```sh
npx remotion render content-studio/assets/overlays/like-share-subscribe/OverlayComposition.tsx LikeShareSubscribe like-share-subscribe.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le
```

The command is a suggested alpha-capable ProRes 4444 export; verify compatibility with your installed Remotion version and FFmpeg. To obtain WebM with alpha, convert the alpha-capable master with an FFmpeg build supporting VP9 alpha:

```sh
ffmpeg -i like-share-subscribe.mov -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -an like-share-subscribe.webm
```

GIF is optional, but its binary transparency is inferior to alpha video. Import the WebM/MOV as a video overlay in Kdenlive or composite the Remotion component directly in a larger Remotion project. No exports have been generated or tested in this commit.

## Timing

0–0.5s enter; ~0.5s like; ~1s share; ~1.7s subscribe; ~2.3s bell; last 0.4s exit. Customize labels, accent, subscribeColor, scale and bottom through component props. No audio. No external brand logos required.
