import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCurrentFrame } from 'remotion';
const COLORS = {
    active: '#58A6FF',
    success: '#3FB950',
    failed: '#F85149',
    disconnected: '#F85149',
};
export function Link({ x, y, width, height = 30, direction = 'right', label, state = 'active', progress, animated = false, active, failed, }) {
    const frame = useCurrentFrame();
    // Resolve legacy props
    let resolvedState = state;
    if (typeof failed === 'boolean' && failed)
        resolvedState = 'failed';
    else if (typeof active === 'boolean' && !active)
        resolvedState = 'success';
    const color = COLORS[resolvedState] ?? COLORS.active;
    const isFailed = resolvedState === 'failed' || resolvedState === 'disconnected';
    const isDisconnected = resolvedState === 'disconnected';
    const drawProgress = typeof progress === 'number' ? Math.max(0, Math.min(1, progress)) : 1;
    const visibleWidth = width * drawProgress;
    const travel = ((frame % 36) / 36);
    // No dot by default — only when explicitly requested
    const dotVisible = animated && (resolvedState === 'active' || resolvedState === 'failed' || resolvedState === 'success');
    const dotX = direction === 'left' ? width * (1 - travel) : width * travel;
    return (_jsxs("div", { style: { position: 'absolute', left: x, top: y, width, height, pointerEvents: 'none', overflow: 'hidden' }, children: [_jsx("div", { style: { position: 'absolute', left: 0, top: 13, width, height: 3, background: `${color}22`, borderRadius: 3, border: isDisconnected ? `1px dashed ${color}` : 'none' } }), _jsx("div", { style: {
                    position: 'absolute',
                    left: 0,
                    top: 13,
                    width: visibleWidth,
                    height: 3,
                    background: isDisconnected ? 'transparent' : color,
                    boxShadow: isDisconnected ? 'none' : `0 0 14px ${color}`,
                    borderRadius: 3,
                    opacity: drawProgress > 0 ? 1 : 0,
                    borderTop: isDisconnected ? `2px dashed ${color}` : 'none',
                    borderBottom: isDisconnected ? `2px dashed ${color}` : 'none',
                    backgroundImage: isDisconnected ? `repeating-linear-gradient(90deg, ${color} 0 8px, transparent 8px 12px)` : undefined,
                } }), dotVisible && drawProgress > 0.05 && (_jsx("div", { style: {
                    position: 'absolute',
                    left: Math.min(dotX, visibleWidth) - 6,
                    top: 7,
                    width: 15,
                    height: 15,
                    borderRadius: '50%',
                    background: color,
                    boxShadow: `0 0 16px ${color}`,
                    opacity: isDisconnected ? 0.5 : 1,
                } })), (direction === 'right' || direction === 'both') && (_jsx("div", { style: {
                    position: 'absolute',
                    right: -1,
                    top: 7,
                    width: 0,
                    height: 0,
                    borderTop: '6px solid transparent',
                    borderBottom: '6px solid transparent',
                    borderLeft: `10px solid ${color}`,
                    opacity: drawProgress > 0.98 ? 1 : 0,
                } })), (direction === 'left' || direction === 'both') && (_jsx("div", { style: {
                    position: 'absolute',
                    left: -1,
                    top: 7,
                    width: 0,
                    height: 0,
                    borderTop: '6px solid transparent',
                    borderBottom: '6px solid transparent',
                    borderRight: `10px solid ${color}`,
                    opacity: drawProgress > 0.98 ? 1 : 0,
                } })), label && (_jsx("div", { style: {
                    position: 'absolute',
                    left: width / 2,
                    top: -8,
                    transform: 'translateX(-50%)',
                    fontSize: 11,
                    fontWeight: 800,
                    letterSpacing: 1,
                    color,
                    background: '#0d1117',
                    padding: '2px 6px',
                    borderRadius: 6,
                    border: `1px solid ${color}55`,
                    whiteSpace: 'nowrap',
                    opacity: drawProgress > 0.2 ? 1 : 0,
                }, children: label })), isFailed && drawProgress > 0.5 && (_jsx("div", { style: {
                    position: 'absolute',
                    left: width / 2 - 10,
                    top: 2,
                    fontSize: 18,
                    fontWeight: 900,
                    color,
                    opacity: 0.9,
                }, children: "\u00D7" }))] }));
}
