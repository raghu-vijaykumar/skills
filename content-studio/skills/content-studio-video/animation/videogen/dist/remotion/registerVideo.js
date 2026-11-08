import { Fragment as _Fragment, jsx as _jsx } from "react/jsx-runtime";
import { Composition, registerRoot } from 'remotion';
import { getAudioDurationInSeconds } from '@remotion/media-utils';
function buildComposition(entry) {
    const { id, component, narrationSrc, narrationCues, width = 1080, height = 1920, fps = 30, followAudioSrc, followDurationFrames = 0 } = entry;
    const durationSeconds = narrationCues[narrationCues.length - 1]?.endSeconds ?? 0;
    return (_jsx(Composition, { id: id, component: component, durationInFrames: Math.max(1, Math.ceil(durationSeconds * fps) + followDurationFrames), fps: fps, width: width, height: height, calculateMetadata: async () => {
            const narrationDuration = await getAudioDurationInSeconds(narrationSrc);
            const followDuration = followAudioSrc ? await getAudioDurationInSeconds(followAudioSrc) : 0;
            return {
                durationInFrames: Math.max(1, Math.ceil(Math.max(durationSeconds, narrationDuration) * fps) + Math.ceil(followDuration * fps)),
            };
        } }, id));
}
export function registerVideoEntry(options) {
    const Root = () => buildComposition(options);
    registerRoot(Root);
    return Root;
}
export function registerVideoCatalog(entries) {
    const Root = () => _jsx(_Fragment, { children: entries.map((entry) => buildComposition(entry)) });
    registerRoot(Root);
    return Root;
}
