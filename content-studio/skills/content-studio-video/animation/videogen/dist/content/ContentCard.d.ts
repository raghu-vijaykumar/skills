import React from 'react';
import type { Theme } from '../project.ts';
export type CardProps = {
    style: string;
    styleName?: string;
    theme?: Theme;
    kind: 'text' | 'image' | 'gif' | 'video';
    phase?: string;
    heading: string;
    body?: string;
    claimKind?: 'observed' | 'inference' | 'limitation' | 'contradicted';
    mediaAsset?: string;
    evidence?: {
        id: string;
        attribution: string;
        capturedAt?: string;
        method?: string;
    };
    startSeconds?: number;
    durationSeconds?: number;
    width?: number;
    height?: number;
};
export declare function ContentCard(props: CardProps): React.JSX.Element;
