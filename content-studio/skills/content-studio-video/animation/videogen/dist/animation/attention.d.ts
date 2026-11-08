import type { AttentionLevel, MotionAction } from './types.ts';
export declare const ATTENTION_RANK: Record<AttentionLevel, number>;
export declare const attentionOpacity: Record<AttentionLevel, number>;
export declare const attentionBrightness: Record<AttentionLevel, number>;
export declare const attentionScale: Record<AttentionLevel, number>;
export declare const attentionGlow: Record<AttentionLevel, number>;
export type EmphasisParams = {
    opacity: number;
    brightness: number;
    scale: number;
    glow: number;
};
export declare function emphasisParams(level: AttentionLevel): EmphasisParams;
export declare const glowStyle: (glow: number, color: string, radius?: number) => string | undefined;
export declare function emphasisForTargets(levels: ReadonlyMap<string, AttentionLevel>): Map<string, EmphasisParams>;
export type AttentionCollision = {
    t: number;
    actions: MotionAction[];
};
export declare function primaryCollisions(actions: readonly MotionAction[], duration: number, step?: number): AttentionCollision[];
