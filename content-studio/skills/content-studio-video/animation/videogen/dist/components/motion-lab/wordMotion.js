import { jsx as _jsx } from "react/jsx-runtime";
/** Find the spoken word on the scene clock. Holds keep the last word visible. */
export function sampleWordMotion(cues, frame) {
    let lower = 0;
    let upper = cues.length;
    while (lower < upper) {
        const center = Math.floor((lower + upper) / 2);
        if (cues[center].startFrame <= frame)
            lower = center + 1;
        else
            upper = center;
    }
    const index = lower - 1;
    const cue = cues[index];
    const elapsed = cue ? frame - cue.startFrame : 0;
    return { cue, index, elapsed, speaking: Boolean(cue && frame < cue.endFrame) };
}
export function WordMotionCaption({ cues, frame, color = '#fff', muted = '#aaabc3', accent = '#373276' }) {
    const { cue, index, elapsed } = sampleWordMotion(cues, frame);
    if (!cue)
        return null;
    return _jsx("div", { "data-word-onset": cue.startFrame, style: {
            position: 'absolute', left: '6%', right: '6%', top: '10%', lineHeight: 1.4,
            textAlign: 'center', fontSize: '4.7cqw', fontWeight: 750, color: muted, pointerEvents: 'none',
        }, children: cues.map((word, i) => i <= index && word.line === cue.line ?
            _jsx("span", { style: {
                    display: 'inline-block', margin: '0 0.09em', borderRadius: '0.14em', padding: '0 0.12em',
                    color: i === index ? color : muted, backgroundColor: i === index ? accent : 'transparent',
                    transform: i === index ? `translateY(${Math.max(0, 1 - elapsed / 4) * 0.16}em)` : undefined,
                }, children: word.text }, word.startFrame) : null) });
}
