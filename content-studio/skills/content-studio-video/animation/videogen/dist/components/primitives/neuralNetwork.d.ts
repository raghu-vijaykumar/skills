export type NetNode = {
    layer: number;
    index: number;
    x: number;
    y: number;
    r: number;
    seed: number;
};
export type NetEdge = {
    id: number;
    from: number;
    to: number;
    layer: number;
    weight: number;
    seed: number;
};
export type NetworkSpec = {
    /** Node count per layer, input first. */
    layerSizes: number[];
    /** X position of each layer column. */
    xs: number[];
    /** Vertical centre of the network. */
    centerY: number;
    /** Vertical distance between adjacent nodes in a layer. */
    gapY: number;
    /** Node radius at rest. */
    radius: number;
    /** How many neighbours in the next layer each node connects to. */
    fanout: number;
};
export type Network = {
    spec: NetworkSpec;
    nodes: NetNode[];
    edges: NetEdge[];
    /** Node indices grouped by layer. */
    layerNodes: number[][];
    /** Left/right extents of the network in its own space. */
    bounds: {
        x: number;
        y: number;
        w: number;
        h: number;
    };
};
export declare function buildNetwork(spec: NetworkSpec): Network;
export type NetworkFrame = {
    /** 0..1 forward signal position (0 = input, 1 = output). */
    forward: number;
    /** 0..1 backward signal position (0 = output, 1 = input). */
    backward: number;
    /** 0..1 weight-update amount. */
    update: number;
    /** 0..1 error strength, gates the backward signal. */
    loss: number;
    /** Optional travelling glow along the axis, 0..1 (null = off). */
    pulse?: number | null;
};
export type NetworkState = {
    nodeActivation: number[];
    nodeBack: number[];
    edgeFlow: number[];
    edgeBack: number[];
    edgeWeight: number[];
    nodeDelta: number[];
    /** Interpolated world position of the travelling pulse, or null. */
    pulse: {
        x: number;
        y: number;
    } | null;
};
export declare function networkStateAt(net: Network, frame: NetworkFrame): NetworkState;
