export type MediaKind = 'image' | 'gif' | 'video' | 'sfx';
export type MediaClip = {
    id: string;
    kind: MediaKind;
    src: string;
    start: number;
    duration: number;
    volume?: number;
    target?: string;
    attention?: 'background' | 'secondary' | 'primary';
};
export type MediaIssue = {
    t: number;
    clip: string;
    msg: string;
    kind: 'error' | 'warn';
};
export declare function activeMediaAt(now: number, clips: readonly MediaClip[]): MediaClip[];
export declare function upcomingMedia(now: number, clips: readonly MediaClip[], horizon?: number): MediaClip[];
export declare function validateMedia(clips: readonly MediaClip[]): MediaIssue[];
export declare function mediaFrame(now: number, clips: readonly MediaClip[]): {
    id: string;
    kind: MediaKind;
    progress: number;
}[];
