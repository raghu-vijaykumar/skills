import React from 'react';
declare const MONO = "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace";
export type TextTiming = {
    start: number;
    end: number;
};
export declare const spanProgress: (now: number, timing: TextTiming) => number;
export declare function WordReveal({ text, now, start, end, fontSize, color, muted, accent, lineHeight, }: {
    text: string;
    now: number;
    start: number;
    end: number;
    fontSize?: number;
    color?: string;
    muted?: string;
    accent?: string;
    lineHeight?: number;
}): React.JSX.Element;
export declare function PhraseReveal({ children, now, start, duration, rise, }: {
    children: React.ReactNode;
    now: number;
    start: number;
    duration?: number;
    rise?: number;
}): React.JSX.Element;
export declare function Emphasis({ children, level, glowColor, style, }: {
    children: React.ReactNode;
    level: 'primary' | 'secondary' | 'background';
    glowColor: string;
    style?: React.CSSProperties;
}): React.JSX.Element;
export declare function CountUp({ value, now, start, duration, easing, style, }: {
    value: number;
    now: number;
    start: number;
    duration?: number;
    easing?: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'backOut';
    style?: React.CSSProperties;
}): React.JSX.Element;
export declare function CodeHighlight({ lines, activeLine, now, start, step, fontSize, activeColor, muted, textColor, lineHeight, }: {
    lines: string[];
    activeLine?: number;
    now?: number;
    start?: number;
    step?: number;
    fontSize?: number;
    activeColor?: string;
    muted?: string;
    textColor?: string;
    lineHeight?: number;
}): React.JSX.Element;
export { MONO };
