// Reusable neural-network visual primitive: a pure, Node-safe model.
//
// A network is a set of vertical node columns (layers) with a representative
// subset of connections between adjacent layers. It is deliberately NOT a full
// mesh: a handful of large nodes and thick, readable connections read far better
// on a phone than hundreds of hairlines.
//
// The model owns the *state* of the network for one instant:
//   - activation : how lit each node is (forward signal arriving)
//   - edgeFlow   : how strongly each connection carries the forward signal
//   - edgeBack   : how strongly each connection carries the backward signal
//   - edgeWeight : the current weight of each connection (base + update delta)
//   - nodeDelta  : the per-node weight change for the update beat
//   - pulse      : a travelling glow along the layer axis (retry / repeat)
//
// Everything is a pure function of (network, frame), so a scene and a validator
// resolve the exact same picture. No DOM, no randomness.

export type NetNode = {layer: number; index: number; x: number; y: number; r: number; seed: number};
export type NetEdge = {id: number; from: number; to: number; layer: number; weight: number; seed: number};

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
  bounds: {x: number; y: number; w: number; h: number};
};

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
const hash01 = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
const gauss = (d: number, w = 0.72) => Math.exp(-((d / w) * (d / w)));

export function buildNetwork(spec: NetworkSpec): Network {
  const nodes: NetNode[] = [];
  const layerNodes: number[][] = [];
  const xs = spec.xs;

  spec.layerSizes.forEach((count, layer) => {
    const indices: number[] = [];
    for (let index = 0; index < count; index += 1) {
      const seed = hash01(layer * 131 + index * 17.3 + 3);
      indices.push(nodes.length);
      nodes.push({
        layer,
        index,
        x: xs[layer],
        y: spec.centerY + (index - (count - 1) / 2) * spec.gapY,
        r: spec.radius * (0.9 + seed * 0.2),
        seed,
      });
    }
    layerNodes.push(indices);
  });

  const edges: NetEdge[] = [];
  for (let layer = 0; layer < spec.layerSizes.length - 1; layer += 1) {
    const a = layerNodes[layer];
    const b = layerNodes[layer + 1];
    a.forEach((fromIdx, ai) => {
      const centre = a.length === 1 ? 0 : Math.round((ai / (a.length - 1)) * (b.length - 1));
      const candidates: number[] = [];
      for (let off = -1; off <= 1; off += 1) {
        const bi = centre + off;
        if (bi >= 0 && bi < b.length && !candidates.includes(bi)) candidates.push(bi);
      }
      // If the layer is wide relative to the fanout, spread the remaining picks.
      while (candidates.length < Math.min(spec.fanout, b.length)) {
        const bi = Math.floor(hash01(fromIdx * 7.1 + candidates.length * 3.3) * b.length);
        if (!candidates.includes(bi)) candidates.push(bi);
        else break;
      }
      candidates.slice(0, spec.fanout).forEach((bi) => {
        const toIdx = b[bi];
        const seed = hash01(fromIdx * 13.7 + toIdx * 5.9 + 1);
        edges.push({
          id: edges.length,
          from: fromIdx,
          to: toIdx,
          layer,
          weight: 0.35 + seed * 0.65,
          seed,
        });
      });
    });
  }

  const minX = Math.min(...nodes.map((n) => n.x - n.r));
  const maxX = Math.max(...nodes.map((n) => n.x + n.r));
  const minY = Math.min(...nodes.map((n) => n.y - n.r));
  const maxY = Math.max(...nodes.map((n) => n.y + n.r));
  return {
    spec,
    nodes,
    edges,
    layerNodes,
    bounds: {x: minX, y: minY, w: maxX - minX, h: maxY - minY},
  };
}

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
  pulse: {x: number; y: number} | null;
};

export function networkStateAt(net: Network, frame: NetworkFrame): NetworkState {
  const layers = net.spec.layerSizes.length;
  const span = Math.max(1, layers - 1);
  const forwardPos = clamp01(frame.forward) * span;
  const backwardPos = (1 - clamp01(frame.backward)) * span;
  const loss = clamp01(frame.loss);

  const nodeActivation = net.nodes.map((n) => clamp01(0.08 + gauss(forwardPos - n.layer)));
  const nodeBack = net.nodes.map((n) => clamp01(gauss(backwardPos - n.layer) * loss));
  const edgeFlow = net.edges.map((e) => clamp01(gauss(forwardPos - (e.layer + 0.5))));
  const edgeBack = net.edges.map((e) => clamp01(gauss(backwardPos - (e.layer + 0.5)) * loss));
  const update = clamp01(frame.update);
  const edgeWeight = net.edges.map((e) => e.weight + (hash01(e.seed * 1000 + 3) - 0.5) * 0.7 * update);
  const nodeDelta = net.nodes.map((n) => (hash01(n.seed * 1000 + 7) - 0.5) * update);

  let pulse: {x: number; y: number} | null = null;
  if (frame.pulse != null) {
    const t = clamp01(frame.pulse) * span;
    const l = Math.min(layers - 2, Math.floor(t));
    const u = t - l;
    const x = net.spec.xs[l] + (net.spec.xs[l + 1] - net.spec.xs[l]) * u;
    pulse = {x, y: net.spec.centerY};
  }

  return {nodeActivation, nodeBack, edgeFlow, edgeBack, edgeWeight, nodeDelta, pulse};
}
