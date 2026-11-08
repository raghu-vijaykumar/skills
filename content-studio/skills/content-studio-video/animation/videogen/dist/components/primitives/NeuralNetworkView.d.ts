import React from 'react';
import type { Network, NetworkState } from './neuralNetwork.ts';
export declare function NeuralNetwork({ net, state, width, height, opacity, tone, errorTone, weightVisible, }: {
    net: Network;
    state: NetworkState;
    width: number;
    height: number;
    opacity?: number;
    tone?: string;
    errorTone?: string;
    /** Draw connections with a width driven by their weight (update beat). */
    weightVisible?: boolean;
}): React.JSX.Element | null;
