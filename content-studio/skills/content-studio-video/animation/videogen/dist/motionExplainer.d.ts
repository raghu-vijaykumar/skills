import React from 'react';
export type ExplainerScene = {
    id: string;
    type: 'hero' | 'device' | 'flow' | 'stack' | 'code' | 'data' | 'document' | 'presenter';
    startFrame: number;
    endFrame: number;
    title: string;
    kicker?: string;
    subtitle?: string;
    visual: {
        symbol?: string;
        nodes?: string[];
        lines?: string[];
        metric?: string;
        note?: string;
        labels?: string[];
        theme?: 'light' | 'dark';
        imageId?: string;
    };
    stateChanges: {
        frame: number;
        label: string;
    }[];
    camera: {
        frame: number;
        scale: number;
        x?: number;
        y?: number;
    }[];
    presenter?: {
        pose?: 'speaking' | 'pointing' | 'thinking' | 'none';
        label?: string;
    };
    assetIds: string[];
    narrationCueIds: string[];
    sourceIds: string[];
    audioCueIds: string[];
};
export type ExplainerPlan = {
    schemaVersion: 1;
    width: number;
    height: number;
    fps: 30;
    durationFrames: number;
    title?: string;
    chapters?: {
        label: string;
        startFrame: number;
    }[];
    scenes: ExplainerScene[];
};
export declare function ExplainerFilm({ plan, renderScene, renderPresenter, presenterImage, presenterImages, media }: {
    plan: ExplainerPlan;
    renderScene?: (scene: ExplainerScene, frame: number) => React.ReactNode;
    presenterImage?: string;
    renderPresenter?: (scene: ExplainerScene, sceneFrame: number) => React.ReactNode;
    presenterImages?: Partial<Record<'speaking' | 'pointing' | 'thinking', string>>;
    media?: Record<string, string>;
}): React.JSX.Element;
