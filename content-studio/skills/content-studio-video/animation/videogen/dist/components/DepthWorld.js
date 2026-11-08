import { jsx as _jsx } from "react/jsx-runtime";
import { useVideoConfig } from 'remotion';
import { projectLayers } from '../animation/depth.js';
export function DepthWorld({ cam, depth, layers, renderLayer, }) {
    const { width, height } = useVideoConfig();
    const projected = projectLayers(layers, cam, depth ?? {}, width, height);
    return (_jsx("div", { style: { position: 'absolute', inset: 0, overflow: 'hidden' }, children: projected.map(({ layer, p }) => (_jsx("div", { style: {
                position: 'absolute',
                left: p.x,
                top: p.y,
                width: p.w,
                height: p.h,
                zIndex: p.zIndex,
                transformOrigin: '0 0',
                filter: p.blur > 0.05 ? `blur(${p.blur.toFixed(2)}px)` : undefined,
            }, children: renderLayer(layer, p) }, layer.id))) }));
}
