import React, { type ComponentType } from 'react';
type Point = readonly [number, number];
type Hand = 'rest' | 'point' | 'open' | 'two';
/** Extension of thumb through little finger. Zero is curled and one is extended. */
export type PresenterFingers = readonly [number, number, number, number, number];
type Arm = {
    elbow: Point;
    wrist: Point;
    angle: number;
    hand: Hand;
    fingers?: PresenterFingers;
};
type Pose = {
    head: number;
    left: Arm;
    right: Arm;
    gaze?: Point;
};
export type PresenterGesture = 'rest' | 'point-left' | 'point-right' | 'explain' | 'two' | 'present';
export type PresenterPoseOverride = {
    head?: number;
    left?: Partial<Arm>;
    right?: Partial<Arm>;
    gaze?: Point;
};
export type PresenterCue = {
    frame: number;
    gesture: PresenterGesture;
    transitionFrames?: number;
    pose?: PresenterPoseOverride;
};
export type PresenterPalette = {
    skin: string;
    skinShade: string;
    shirt: string;
    shirtShade: string;
};
export type PresenterFaceProps = {
    eyeOpen: number;
    mouthOpen: number;
    gaze: number;
    /** Vertical gaze in rig coordinates. Positive values look down. */
    gazeY?: number;
    palette: PresenterPalette;
};
export type PresenterBodyProps = {
    left: Arm;
    right: Arm;
    palette: PresenterPalette;
};
/** Each cue starts from the pose already visible on that frame. */
export declare function samplePresenterPose(cues: readonly PresenterCue[], frame: number): Pose;
export type Presenter2DProps = {
    frame: number;
    face: ComponentType<PresenterFaceProps>;
    body?: ComponentType<PresenterBodyProps>;
    /** Draw a front-facing limb from the same sampled pose after the head. */
    foreground?: ComponentType<PresenterBodyProps>;
    /** Ordered cues use the composition's scene-local frame clock. */
    cues?: readonly PresenterCue[];
    blinkFrames?: readonly number[];
    /** Normalized speech energy. An explicit mouthOpen value can drive custom mouth timing. */
    speech?: number;
    mouthOpen?: number;
    x?: number;
    y?: number;
    scale?: number;
    palette?: Partial<PresenterPalette>;
};
/** SVG group anchored at the base of the head. Put it inside the scene SVG. */
export declare function Presenter2D({ frame, face: Face, body: Body, foreground: Foreground, cues, blinkFrames, speech, mouthOpen, x, y, scale, palette: paletteOverride }: Presenter2DProps): React.JSX.Element;
export {};
