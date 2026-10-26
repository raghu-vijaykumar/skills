// Media & SFX as first-class choreography elements (§17).
//
// A video's timeline may export `mediaSource(cues)` returning a list of clips.
// MediaClips are pure declarations (kind/src/start/duration); validators and
// scenes resolve them deterministically. Nothing here depends on Remotion, so
// Node can audit clips the same way it audits motion events.

export type MediaKind = 'image' | 'gif' | 'video' | 'sfx';

export type MediaClip = {
  id: string;
  kind: MediaKind;
  src: string;
  start: number; // seconds
  duration: number; // seconds
  volume?: number; // 0..1, sfx only
  target?: string; // semantic object it accompanies
  attention?: 'background' | 'secondary' | 'primary';
};

export type MediaIssue = {t: number; clip: string; msg: string; kind: 'error' | 'warn'};

export function activeMediaAt(now: number, clips: readonly MediaClip[]): MediaClip[] {
  return clips.filter((clip) => now >= clip.start && now < clip.start + clip.duration);
}

export function upcomingMedia(now: number, clips: readonly MediaClip[], horizon = 2): MediaClip[] {
  return clips.filter((clip) => clip.start >= now && clip.start <= now + horizon);
}

// Deterministic validation: sane windows, non-empty sources, and no SFX pile-up.
export function validateMedia(clips: readonly MediaClip[]): MediaIssue[] {
  const issues: MediaIssue[] = [];
  for (const clip of clips) {
    if (!Number.isFinite(clip.start) || clip.start < 0) issues.push({t: clip.start, clip: clip.id, msg: 'start is not finite/non-negative', kind: 'error'});
    if (!Number.isFinite(clip.duration) || clip.duration <= 0.02) issues.push({t: clip.start, clip: clip.id, msg: 'duration must be > 0', kind: 'error'});
    if (!clip.src) issues.push({t: clip.start, clip: clip.id, msg: 'missing src', kind: 'error'});
    if (clip.kind === 'sfx' && clip.volume != null && (clip.volume < 0 || clip.volume > 1)) issues.push({t: clip.start, clip: clip.id, msg: 'sfx volume outside 0..1', kind: 'error'});
  }
  // Two SFX overlapping the same instant is an attention collision.
  const sfx = clips.filter((clip) => clip.kind === 'sfx').sort((a, b) => a.start - b.start);
  for (let i = 0; i < sfx.length; i += 1) {
    for (let j = i + 1; j < sfx.length; j += 1) {
      if (sfx[i].start + sfx[i].duration > sfx[j].start + 1e-6 && sfx[i].start < sfx[j].start + sfx[j].duration) {
        issues.push({t: sfx[j].start, clip: sfx[j].id, msg: `overlaps sfx "${sfx[i].id}"`, kind: 'warn'});
      }
    }
  }
  return issues;
}

// Frame-resolvable media state: clips active at `now`, as part of the frame
// state graph when a video supplies media.
export function mediaFrame(now: number, clips: readonly MediaClip[]): {id: string; kind: MediaKind; progress: number}[] {
  return activeMediaAt(now, clips).map((clip) => ({
    id: clip.id,
    kind: clip.kind,
    progress: Math.max(0, Math.min(1, (now - clip.start) / clip.duration)),
  }));
}
