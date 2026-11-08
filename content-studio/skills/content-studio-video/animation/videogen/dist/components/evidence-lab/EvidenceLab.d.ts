import React from 'react';
export type CapturedEvidence = {
    src: string;
    kind: 'image' | 'video';
    meta: {
        id: string;
        attribution?: string | null;
        evidence?: {
            capturedAt?: string;
            method?: string;
        } | null;
    };
    startFrom?: number;
    sequenceFrom?: number;
};
export declare function EvidenceLabFrame({ children, phase }: {
    children: React.ReactNode;
    phase: 'QUESTION' | 'METHOD' | 'RUN' | 'FINDING' | 'LIMIT';
}): React.JSX.Element;
export declare function EvidenceCapture({ asset, x, y, width, height }: {
    asset: CapturedEvidence;
    x: number;
    y: number;
    width: number;
    height: number;
}): React.JSX.Element;
export declare function EvidenceFinding({ kind, children, x, y, width }: {
    kind: 'observed' | 'inference' | 'limitation' | 'contradicted';
    children: React.ReactNode;
    x: number;
    y: number;
    width: number;
}): React.JSX.Element;
