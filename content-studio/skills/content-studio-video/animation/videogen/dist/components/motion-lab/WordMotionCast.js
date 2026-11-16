import { Fragment as _Fragment, jsx as _jsx } from "react/jsx-runtime";
/** Swap actor artwork while keeping paint order and the compiled rig values. */
export function WordMotionCast({ choreography, art, frame }) {
    return _jsx(_Fragment, { children: choreography.actorIds.map(actor => {
            if (!Object.hasOwn(art, actor) || !art[actor])
                throw new Error(`Art preset is missing actor ${actor}`);
            const Art = art[actor];
            return _jsx(Art, { frame: frame, channels: choreography.sample(actor, frame) }, actor);
        }) });
}
