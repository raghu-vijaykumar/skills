export type Point = {
    x: number;
    y: number;
};
export type Rect = {
    x: number;
    y: number;
    w: number;
    h: number;
};
export type PathKind = 'linear' | 'arc' | 'bezier' | 'orthogonal' | 'curved' | 'follow-link';
export type PathOptions = {
    sagitta?: number;
    control?: Point[];
    firstAxis?: 'x' | 'y';
    waypoints?: Point[];
    segments?: number;
};
export type Path = {
    kind: PathKind;
    a: Point;
    b: Point;
    pointAt: (u: number) => Point;
    samples: (n?: number) => Point[];
    length: () => number;
    bounds: () => Rect;
    offsetPoint: (u: number, normalOffset: number) => Point;
};
export declare function buildPath(kind: PathKind, a: Point, b: Point, options?: PathOptions): Path;
