import React from 'react';
import {Img, OffthreadVideo, staticFile, useVideoConfig} from 'remotion';
import {BG, BG_ELEVATED, BORDER, CYAN, GREEN, MUTED, RED, TEXT, YELLOW} from '../design/color.ts';
import {FONT_MONO, FONT_SANS} from '../design/typography.ts';
import {loadAppFonts} from '../design/fonts.ts';
import type {Theme} from '../project.ts';

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
  evidence?: {id: string; attribution: string; capturedAt?: string; method?: string};
  startSeconds?: number;
  durationSeconds?: number;
  width?: number;
  height?: number;
};

// Shared content cards use the same dark foundation as video. Real media stays
// untouched inside a contain-fit window; claims and citations sit outside it.
export function ContentCard(props: CardProps) {
  // The compatibility preset uses bundled local fonts; neutral and custom
  // themes can use their own font registration without loading channel assets.
  if (props.theme?.id === 'revise-labs') loadAppFonts();
  const {width, height, fps} = useVideoConfig();
  const palette = props.theme?.colors;
  const brand = props.theme?.brand ?? '';
  const title = props.styleName ?? props.style.replace(/-/g, ' ').toUpperCase();
  const s = width / 1080;
  const media = props.mediaAsset ? staticFile(props.mediaAsset) : null;
  const hasMedia = props.kind !== 'text' && Boolean(media);
  const accent = props.claimKind === 'observed' ? (palette?.success ?? GREEN) : props.claimKind === 'limitation' ? (palette?.warning ?? YELLOW) : props.claimKind === 'contradicted' ? (palette?.danger ?? RED) : (palette?.accent ?? CYAN);
  const source = props.evidence;
  const mastheadY = height * 0.047;
  const titleY = height * 0.165;
  const mediaY = height * 0.39;
  const mediaH = height * 0.44;
  const mediaX = 64 * s;
  const mediaW = width - mediaX * 2;
  return <div style={{position: 'absolute', inset: 0, background: palette?.background ?? BG, color: palette?.text ?? TEXT, fontFamily: props.theme?.fonts.sans ?? FONT_SANS, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 64 * s, right: 64 * s, top: 40 * s, height: 4 * s, background: accent}} />
    <div style={{position: 'absolute', left: 64 * s, top: mastheadY, color: accent, fontFamily: props.theme?.fonts.mono ?? FONT_MONO, fontSize: 23 * s, fontWeight: 800, letterSpacing: 2 * s}}>{brand ? `${brand} / ` : ''}{title.toUpperCase()}</div>
    <div style={{position: 'absolute', left: 64 * s, top: height * 0.115, color: palette?.muted ?? MUTED, fontFamily: props.theme?.fonts.mono ?? FONT_MONO, fontSize: 25 * s, letterSpacing: 2 * s, textTransform: 'uppercase'}}>{props.phase ?? props.claimKind ?? 'INSIGHT'}</div>
    <div style={{position: 'absolute', left: 64 * s, right: 64 * s, top: titleY, fontSize: (hasMedia ? 54 : 66) * s, fontWeight: 900, letterSpacing: -1.1 * s, lineHeight: 1.06}}>{props.heading}</div>
    {hasMedia ? <>
      {props.body ? <div style={{position: 'absolute', left: 68 * s, right: 68 * s, top: height * 0.325, fontSize: 30 * s, fontWeight: 650, lineHeight: 1.25, color: palette?.muted ?? MUTED}}>{props.body}</div> : null}
      <div style={{position: 'absolute', left: mediaX, top: mediaY, width: mediaW, height: mediaH, border: `${2 * s}px solid ${palette?.border ?? BORDER}`, borderRadius: 18 * s, overflow: 'hidden', background: palette?.elevated ?? BG_ELEVATED, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {props.kind === 'image' ? <Img src={media!} style={{width: '100%', height: '100%', objectFit: 'contain'}} /> : <OffthreadVideo src={media!} muted startFrom={Math.round((props.startSeconds ?? 0) * fps)} style={{width: '100%', height: '100%', objectFit: 'contain'}} />}
      </div>
      <div style={{position: 'absolute', left: mediaX, right: mediaX, top: height * 0.855, fontFamily: props.theme?.fonts.mono ?? FONT_MONO, fontSize: 22 * s, color: palette?.muted ?? MUTED, lineHeight: 1.28}}>
        <div style={{color: palette?.text ?? TEXT, fontWeight: 800}}>SOURCE {source?.id ?? 'UNREGISTERED'}{source?.capturedAt ? ` · ${source.capturedAt}` : ''}</div>
        <div>{source?.attribution ?? ''}{source?.method ? ` · ${source.method}` : ''}</div>
      </div>
    </> : <div style={{position: 'absolute', left: 72 * s, right: 72 * s, top: height * 0.43, borderLeft: `${7 * s}px solid ${accent}`, paddingLeft: 30 * s, fontSize: 46 * s, lineHeight: 1.22, fontWeight: 700}}>{props.body}</div>}
    <div style={{position: 'absolute', left: 64 * s, right: 64 * s, bottom: 45 * s, height: 1 * s, background: palette?.border ?? BORDER}} />
    <div style={{position: 'absolute', left: 64 * s, bottom: 18 * s, color: palette?.muted ?? MUTED, fontFamily: props.theme?.fonts.mono ?? FONT_MONO, fontSize: 19 * s, letterSpacing: 1.5 * s}}>{brand}</div>
  </div>;
}
