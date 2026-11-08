import type { MotionAction } from './types.ts';
export declare function cloneAction(action: MotionAction): MotionAction;
export declare function delayed(action: MotionAction, by: number): MotionAction;
export declare function after(action: MotionAction, trigger: MotionAction): MotionAction;
export declare function sequence(start: number, actions: readonly MotionAction[]): MotionAction[];
export declare function stagger(start: number, step: number, actions: readonly MotionAction[]): MotionAction[];
export declare function parallel(start: number, actions: readonly MotionAction[]): MotionAction[];
export declare function compileActions(actions: readonly MotionAction[]): MotionAction[];
