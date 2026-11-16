import type {WordMotionCue} from './wordMotion.tsx';
import {progress, smooth} from './objectMotion.tsx';

export type WordChannels = Readonly<Record<string, number>>;
export type WordTarget = number | Readonly<{to: number; frames: number; ease?: 'linear' | 'smooth'}>;
export type WordActor = Readonly<{
  initial: WordChannels;
  actions: Readonly<Record<string, Readonly<Record<string, WordTarget>>>>;
}>;

type Transition = {frame: number; from: number; to: number; frames: number; ease: 'linear' | 'smooth'};
type Track = {initial: number; transitions: Transition[]};

function sampleTrack(track: Track, frame: number): number {
  const transitions = track.transitions;
  let lower = 0;
  let upper = transitions.length;
  while (lower < upper) {
    const center = Math.floor((lower + upper) / 2);
    if (transitions[center].frame <= frame) lower = center + 1;
    else upper = center;
  }
  const transition = transitions[lower - 1];
  if (!transition) return track.initial;
  const {from, to, frame: start, frames, ease} = transition;
  if (frame >= start + frames) return to;
  const amount = (ease === 'smooth' ? smooth : progress)(frame, start, start + frames);
  return from + (to - from) * amount;
}

/** Compile once on the same frame clock as the audio. Sample in any render order. */
export function compileWordChoreography(
  words: readonly WordMotionCue[],
  actors: Readonly<Record<string, WordActor>>,
) {
  const tracks = new Map(Object.entries(actors).map(([actor, definition]) => [actor,
    new Map(Object.entries(definition.initial).map(([channel, initial]): [string, Track] => {
      if (!Number.isFinite(initial)) throw new Error(`${actor}.${channel}: expected a finite initial value`);
      return [channel, {initial, transitions: []}];
    })),
  ]));

  let previous = -1;
  for (const {startFrame, endFrame, text, actor, action} of words) {
    if (!Number.isSafeInteger(startFrame) || !Number.isSafeInteger(endFrame) ||
        startFrame <= previous || endFrame <= startFrame) {
      throw new Error(`${text}: expected ordered word frames with a distinct onset and positive duration`);
    }
    previous = startFrame;
    const channels = tracks.get(actor);
    if (!channels) throw new Error(`${text}: missing actor ${actor}`);
    const actions = actors[actor].actions;
    if (!Object.hasOwn(actions, action)) throw new Error(`${text}: missing action ${actor}.${action}`);
    const targets = Object.entries(actions[action]);
    if (!targets.length) throw new Error(`${actor}.${action}: expected at least one channel target`);
    for (const [channel, target] of targets) {
      const track = channels.get(channel);
      const label = `${actor}.${action}.${channel}`;
      if (!track) throw new Error(`${label}: missing initial channel`);
      if (target == null) throw new Error(`${label}: missing target`);
      const {to, frames, ease = 'linear'} = typeof target === 'number' ? {to: target, frames: 0} : target;
      if (!Number.isFinite(to) || !Number.isSafeInteger(frames) || frames < 0 ||
          (ease !== 'linear' && ease !== 'smooth')) {
        throw new Error(`${label}: invalid target, frame duration, or easing`);
      }
      // An interruption inherits the actual pose. Other channels keep their own motion.
      const from = sampleTrack(track, startFrame);
      track.transitions.push({frame: startFrame, from, to, frames, ease});
    }
  }

  return {
    actorIds: Object.freeze([...tracks.keys()]),
    sample(actor: string, frame: number): WordChannels {
      const channels = tracks.get(actor);
      if (!channels) throw new Error(`Missing actor ${actor}`);
      return Object.fromEntries(Array.from(channels, ([id, track]) => [id, sampleTrack(track, frame)]));
    },
  };
}

export type WordChoreography = ReturnType<typeof compileWordChoreography>;
