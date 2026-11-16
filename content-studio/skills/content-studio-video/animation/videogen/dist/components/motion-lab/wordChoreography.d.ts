import type { WordMotionCue } from './wordMotion.tsx';
export type WordChannels = Readonly<Record<string, number>>;
export type WordTarget = number | Readonly<{
    to: number;
    frames: number;
    ease?: 'linear' | 'smooth';
}>;
export type WordActor = Readonly<{
    initial: WordChannels;
    actions: Readonly<Record<string, Readonly<Record<string, WordTarget>>>>;
}>;
/** Compile once on the same frame clock as the audio. Sample in any render order. */
export declare function compileWordChoreography(words: readonly WordMotionCue[], actors: Readonly<Record<string, WordActor>>): {
    actorIds: readonly string[];
    sample(actor: string, frame: number): WordChannels;
    /** Inspect planned motion before the next word takes focus. Use the exclusive end of this shot's clock. */
    inspectWordActions(endFrame: number): {
        startFrame: number;
        text: string;
        actor: string;
        action: string;
        changedChannels: string[];
    }[];
};
export type WordChoreography = ReturnType<typeof compileWordChoreography>;
