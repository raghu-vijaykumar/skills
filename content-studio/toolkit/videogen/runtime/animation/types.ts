export type EasingName = 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'backOut';

export type AttentionLevel = 'background' | 'secondary' | 'primary';

export type ActionKind =
  | 'appear'
  | 'disappear'
  | 'move'
  | 'scale'
  | 'rotate'
  | 'highlight'
  | 'pulse'
  | 'count'
  | 'visit'
  | 'mark'
  | 'draw'
  | 'reveal'
  | 'morph'
  | 'split'
  | 'merge'
  | 'shake'
  | 'camera-focus'
  | 'camera-zoom'
  | 'text';

export type MotionAction = {
  id: string;
  kind: ActionKind;
  start: number;
  duration: number;
  target?: string;
  from?: number;
  to?: number;
  easing?: EasingName;
  attention?: AttentionLevel;
  dependsOn?: string[];
};

export type TeachingBeat = {
  id: string;
  cueId: string;
  start: number;
  end: number;
  actions: MotionAction[];
};

export type NarrationCue = {
  id: string;
  text: string;
  startSeconds: number;
  endSeconds: number;
};

export type ResolvedAction = MotionAction & {
  progress: number;
  active: boolean;
  complete: boolean;
};

// A single semantic moment on the motion record. This is the unit the
// motion-quality validator reasons about (dead intervals, dwell, attention).
export type MotionEvent = {
  t: number;
  kind: ActionKind | 'phrase';
  target?: string;
  duration: number;
  attention?: AttentionLevel;
};

// The motion record contract: a pure, Node-importable description of every
// meaningful event in a video plus the narration cues that bound them. New
// semantic videos export a `motionSource` builder from their timeline so the
// validator never depends on rendering.
export type MotionSource = {
  cues: readonly NarrationCue[];
  events: MotionEvent[];
  // Deliberate resting windows (short beats with nothing animating).
  rests?: {start: number; end: number}[];
};
