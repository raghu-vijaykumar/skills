import { progress, smooth } from './objectMotion.js';
function sampleTrack(track, frame) {
    const transitions = track.transitions;
    let lower = 0;
    let upper = transitions.length;
    while (lower < upper) {
        const center = Math.floor((lower + upper) / 2);
        if (transitions[center].frame <= frame)
            lower = center + 1;
        else
            upper = center;
    }
    const transition = transitions[lower - 1];
    if (!transition)
        return track.initial;
    const { from, to, frame: start, frames, ease } = transition;
    if (frame >= start + frames)
        return to;
    const amount = (ease === 'smooth' ? smooth : progress)(frame, start, start + frames);
    return from + (to - from) * amount;
}
/** Compile once on the same frame clock as the audio. Sample in any render order. */
export function compileWordChoreography(words, actors) {
    const tracks = new Map(Object.entries(actors).map(([actor, definition]) => [actor,
        new Map(Object.entries(definition.initial).map(([channel, initial]) => {
            if (!Number.isFinite(initial))
                throw new Error(`${actor}.${channel}: expected a finite initial value`);
            return [channel, { initial, transitions: [] }];
        })),
    ]));
    const wordActions = [];
    let previous = -1;
    for (const cue of words) {
        const { startFrame, endFrame, text, actor, action } = cue;
        if (!Number.isSafeInteger(startFrame) || !Number.isSafeInteger(endFrame) ||
            startFrame <= previous || endFrame <= startFrame) {
            throw new Error(`${text}: expected ordered word frames with a distinct onset and positive duration`);
        }
        previous = startFrame;
        const channels = tracks.get(actor);
        if (!channels)
            throw new Error(`${text}: missing actor ${actor}`);
        const actions = actors[actor].actions;
        if (!Object.hasOwn(actions, action))
            throw new Error(`${text}: missing action ${actor}.${action}`);
        const targets = Object.entries(actions[action]);
        if (!targets.length)
            throw new Error(`${actor}.${action}: expected at least one channel target`);
        const actionTracks = targets.map(([channel, target]) => {
            const track = channels.get(channel);
            const label = `${actor}.${action}.${channel}`;
            if (!track)
                throw new Error(`${label}: missing initial channel`);
            if (target == null)
                throw new Error(`${label}: missing target`);
            const { to, frames, ease = 'linear' } = typeof target === 'number' ? { to: target, frames: 0 } : target;
            if (!Number.isFinite(to) || !Number.isSafeInteger(frames) || frames < 0 ||
                (ease !== 'linear' && ease !== 'smooth')) {
                throw new Error(`${label}: invalid target, frame duration, or easing`);
            }
            // An interruption inherits the actual pose. Other channels keep their own motion.
            const from = sampleTrack(track, startFrame);
            const transition = { frame: startFrame, from, to, frames, ease };
            track.transitions.push(transition);
            return { channel, track, transition };
        });
        wordActions.push({ cue: { ...cue }, targets: actionTracks });
    }
    return {
        actorIds: Object.freeze([...tracks.keys()]),
        sample(actor, frame) {
            const channels = tracks.get(actor);
            if (!channels)
                throw new Error(`Missing actor ${actor}`);
            return Object.fromEntries(Array.from(channels, ([id, track]) => [id, sampleTrack(track, frame)]));
        },
        /** Inspect planned motion before the next word takes focus. Use the exclusive end of this shot's clock. */
        inspectWordActions(endFrame) {
            if (!Number.isSafeInteger(endFrame) || endFrame < 1 ||
                wordActions.some(({ cue }) => cue.endFrame > endFrame)) {
                throw new Error('Expected an exclusive end frame covering every word in this shot');
            }
            return wordActions.map(({ cue, targets }, index) => {
                const last = (wordActions[index + 1]?.cue.startFrame ?? endFrame) - 1;
                // Credit only the channels this word actually changes, even while unrelated channels move.
                const changedChannels = targets.filter(({ track, transition }) => sampleTrack(track, last) !== transition.from).map(({ channel }) => channel);
                return { startFrame: cue.startFrame, text: cue.text, actor: cue.actor, action: cue.action, changedChannels };
            });
        },
    };
}
