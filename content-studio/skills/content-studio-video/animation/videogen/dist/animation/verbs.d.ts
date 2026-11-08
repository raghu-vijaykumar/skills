import type { MotionAction } from './types.ts';
import { type CameraShot, type Rect } from './camera.ts';
export declare function visitSequence(prefix: string, targets: string[], start: number, step?: number): MotionAction[];
export declare function processMarks(prefix: string, targets: string[], start: number, step?: number): MotionAction[];
export declare function queueReveal(prefix: string, targets: string[], start: number, step?: number): MotionAction[];
export declare function releaseEdges(prefix: string, edges: {
    from: string;
    to: string;
}[], start: number, per?: number): MotionAction[];
export declare function compareView(id: string, regions: Rect[], start: number, duration: number, width: number, height: number): CameraShot;
