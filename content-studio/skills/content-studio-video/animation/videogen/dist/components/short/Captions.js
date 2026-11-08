import { jsx as _jsx } from "react/jsx-runtime";
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { MUTED, TEXT } from '../../design/color.js';
import { FONT_SANS, LINE_HEIGHT, TYPE, WEIGHT } from '../../design/typography.js';
import { BAND } from '../../design/surfaces.js';
// Shared caption bar, shown below the title in the reserved caption band so it
// never collides with the visual. Displays the current narration phrase
// word-by-word, driven by generated cue timing.
export function Captions({ cues, y = BAND.captionY, fontSize = TYPE.caption, }) {
    const frame = useCurrentFrame();
    const { fps, height } = useVideoConfig();
    const t = frame / fps;
    const active = cues.find((c) => t >= c.startSeconds && t < c.endSeconds);
    if (!active)
        return null;
    const progress = Math.max(0, Math.min(1, (t - active.startSeconds) / Math.max(0.001, active.endSeconds - active.startSeconds)));
    const words = active.text.split(/\s+/);
    const spoken = Math.floor(progress * words.length);
    return (_jsx("div", { "data-captions": true, style: {
            position: 'absolute',
            left: '50%',
            top: y * height,
            transform: 'translateX(-50%)',
            width: '86%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: '0 8px',
            textAlign: 'center',
            lineHeight: LINE_HEIGHT.caption,
            pointerEvents: 'none',
            fontFamily: FONT_SANS,
        }, children: words.map((word, i) => {
            const done = i < spoken;
            const isCurrent = i === spoken;
            return (_jsx("span", { style: {
                    fontSize,
                    fontWeight: WEIGHT.extraBold,
                    color: isCurrent ? TEXT : done ? TEXT : MUTED,
                    opacity: isCurrent ? 1 : done ? 0.92 : 0.55,
                    background: isCurrent ? 'rgba(13,17,23,0.9)' : 'transparent',
                    padding: isCurrent ? '2px 6px' : 0,
                    borderRadius: 6,
                }, children: word }, i));
        }) }));
}
