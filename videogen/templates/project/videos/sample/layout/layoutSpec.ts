// The starter's single title is centered in the composition. Replace this
// geometry with the real scene's semantic layout as the video is authored.
export function layoutFor(_t: number, width: number, height: number) {
  return {
    name: 'starter',
    boxes: [{label: 'story-title', x: width / 2 - 270, y: height / 2 - 60, w: 540, h: 120, kind: 'region', space: 'screen'}],
    links: [],
  };
}
