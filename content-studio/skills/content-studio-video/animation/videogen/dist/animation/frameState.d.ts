import type { AttentionLevel, MotionAction, ResolvedAction } from './types.ts';
import { type CameraShot, type Rect, type CameraTransform } from './camera.ts';
import { type EmphasisParams } from './attention.ts';
import type { Path } from './path.ts';
import { type MediaClip } from './media.ts';
export type ScreenBox = {
    rect: Rect;
    screen: Rect;
    onScreen: boolean;
};
export type FrameGeometry = {
    id: string;
    rect: Rect;
};
export type FramePath = {
    id: string;
    path: Path;
    activeFrom?: number;
    activeTo?: number;
    connects?: {
        from?: string;
        to?: string;
    };
};
export type FrameTypography = {
    id: string;
    start: number;
    end: number;
};
export type FrameInputs = {
    t: number;
    width: number;
    height: number;
    actions?: readonly MotionAction[];
    shots?: readonly CameraShot[];
    geometry?: FrameGeometry[];
    paths?: FramePath[];
    typography?: FrameTypography[];
    media?: readonly MediaClip[];
};
export type ResolvedFrame = {
    t: number;
    width: number;
    height: number;
    resolved: ResolvedAction[];
    active: ResolvedAction[];
    primary: ResolvedAction[];
    attention: Map<string, AttentionLevel>;
    emphasis: Map<string, EmphasisParams>;
    camera: CameraTransform;
    visible: Rect;
    geometry: {
        id: string;
        box: ScreenBox;
    }[];
    paths: {
        id: string;
        active: boolean;
        progress: number;
        point: {
            x: number;
            y: number;
        };
        bounds: Rect;
    }[];
    typography: {
        id: string;
        progress: number;
    }[] | null;
    media: {
        id: string;
        kind: MediaClip['kind'];
        progress: number;
    }[] | null;
};
export declare function resolveFrame(inputs: FrameInputs): ResolvedFrame;
export type FrameIssue = {
    t: number;
    msg: string;
    kind: 'error' | 'warn';
};
export declare function pathCollisionReport(frame: ResolvedFrame, inputs: FrameInputs, pad?: number): FrameIssue[];
export declare function cameraContinuityReport(shots: readonly CameraShot[], width: number, height: number, step?: number, maxJump?: number): FrameIssue[];
export declare function cameraReadabilityReport(frame: ResolvedFrame, inputs: FrameInputs, minScale?: number): FrameIssue[];
export declare function cameraAttentionConflictReport(frame: ResolvedFrame, minScale?: number): FrameIssue[];
