import type { AttentionLevel, MotionAction, ResolvedAction, TeachingBeat } from './types.ts';
export declare function actionProgress(now: number, action: MotionAction): number;
export declare function resolveActions(now: number, actions: readonly MotionAction[]): ResolvedAction[];
export declare function resolveBeats(now: number, beats: readonly TeachingBeat[]): TeachingBeat | null;
export declare function attentionFor(now: number, actions: readonly MotionAction[]): Map<string, AttentionLevel>;
export declare function interpolateAction(now: number, action: MotionAction, fallback?: number): number;
export type FrameState = {
    now: number;
    resolved: ResolvedAction[];
    attention: Map<string, AttentionLevel>;
    active: ResolvedAction[];
    primary: ResolvedAction[];
};
export declare function frameState(now: number, actions: readonly MotionAction[]): FrameState;
