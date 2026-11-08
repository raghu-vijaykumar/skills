import { Fragment as _Fragment, jsx as _jsx } from "react/jsx-runtime";
import { Audio, Img, Sequence, Video } from 'remotion';
// Mounts declared MediaClips (sfx/image/gif/video) as Remotion <Sequence>s so
// media and SFX are deterministic first-class elements of a composition.
export function MediaLayer({ clips, fps }) {
    return (_jsx(_Fragment, { children: clips.map((clip) => {
            const from = Math.round(clip.start * fps);
            const frames = Math.max(1, Math.round(clip.duration * fps));
            if (clip.kind === 'sfx') {
                return (_jsx(Sequence, { from: from, durationInFrames: frames, children: _jsx(Audio, { src: clip.src, volume: clip.volume ?? 0.5 }) }, clip.id));
            }
            if (clip.kind === 'video') {
                return (_jsx(Sequence, { from: from, durationInFrames: frames, children: _jsx(Video, { src: clip.src, style: { position: 'absolute', inset: 0 } }) }, clip.id));
            }
            return (_jsx(Sequence, { from: from, durationInFrames: frames, children: _jsx(Img, { src: clip.src, style: { position: 'absolute', inset: 0 } }) }, clip.id));
        }) }));
}
