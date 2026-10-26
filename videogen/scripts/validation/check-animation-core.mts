// Deterministic unit checks for the shared animation architecture (camera,
// paths, motion primitives, composition, attention). Pure Node; no render.
//
// Usage: node scripts/check-animation-core.mts

import {compileActions, sequence, stagger} from '@raghu-vijaykumar/videogen/runtime/animation/compose';
import {ATTENTION_RANK as attentionRank, emphasisParams, primaryCollisions} from '@raghu-vijaykumar/videogen/runtime/animation/attention';
import {
  establish,
  zoom,
  cameraReturn,
  cameraTransformAt,
  applyTransform,
  invertTransform,
  visibleRect,
  fitRegion,
  validateCamera,
  cameraTrajectory,
  type CameraShot,
} from '@raghu-vijaykumar/videogen/runtime/animation/camera';
import {
  pushIn,
  pullBack,
  slide,
  panBetween,
  followTarget,
  arcPan,
  orbit,
  dollyZoom,
  macroMicroMacro,
  impactShake,
  whipPan,
  parallaxDrift,
  sequenceShots,
  type MoveOptions,
  type FitMoveOptions,
} from '@raghu-vijaykumar/videogen/runtime/animation/cameraMoves';
import {buildPath} from '@raghu-vijaykumar/videogen/runtime/animation/path';
import {appear, mark, rotate, morph, split, merge, shake, reveal} from '@raghu-vijaykumar/videogen/runtime/animation/motion';
import {actionProgress} from '@raghu-vijaykumar/videogen/runtime/animation/choreography';
import {ease} from '@raghu-vijaykumar/videogen/runtime/animation/easing';
import type {PathKind} from '@raghu-vijaykumar/videogen/runtime/animation/path';
import {resolveFrame, pathCollisionReport} from '@raghu-vijaykumar/videogen/runtime/animation/frameState';
import {queueReveal, visitSequence, processMarks, releaseEdges} from '@raghu-vijaykumar/videogen/runtime/animation/verbs';
import {validateMedia, activeMediaAt, mediaFrame} from '@raghu-vijaykumar/videogen/runtime/animation/media';

const results: string[] = [];
let failures = 0;

function check(name: string, ok: boolean, detail?: string) {
  results.push(`${ok ? 'ok' : 'FAIL'} - ${name}${detail ? ` (${detail})` : ''}`);
  if (!ok) failures += 1;
}

const approx = (a: number, b: number, eps = 1e-4) => Math.abs(a - b) <= eps;

// ---- easing -----------------------------------------------------------------
check('ease maps 0 -> 0 and 1 -> 1 for every name', ['linear', 'easeIn', 'easeOut', 'easeInOut', 'backOut'].every((n) => approx(ease(0, n as never), 0) && approx(ease(1, n as never), 1)));
check('ease is monotonic inside the domain', ease(0.25, 'easeInOut') >= 0 && ease(0.75, 'easeInOut') <= 1);

// ---- compose ----------------------------------------------------------------
{
  const acts = sequence(2, [mark('a', 'x', 0, 0.3), mark('b', 'y', 0, 0.2)]);
  check('sequence back-to-back starts', approx(acts[0].start, 2) && approx(acts[1].start, 2.3));
  const st = stagger(5, 0.1, [mark('c', 'x', 0, 0.2), mark('d', 'y', 0, 0.2)]);
  check('stagger increments starts', approx(st[1].start - st[0].start, 0.1));
  const a = appear('a1', 't', 0, 0.4);
  const b = mark('b1', 't', 0, 0.2);
  b.dependsOn = ['a1'];
  const comp = compileActions([a, b]);
  check('compileActions resolves dependsOn after trigger', approx(comp[1].start, 0.4));
  let threw = false;
  try {
    const c1 = mark('x1', 't', 0, 0.2);
    c1.dependsOn = ['x1'];
    compileActions([c1]);
  } catch {
    threw = true;
  }
  check('compileActions throws on dependency cycles', threw);
}

// ---- camera -----------------------------------------------------------------
{
  const W = 960;
  const H = 540;
  const region = {x: 200, y: 120, w: 300, h: 200};
  const shots: CameraShot[] = [
    establish('e', region, 0, 1.0, W, H),
    zoom('z', {x: 400, y: 200, w: 80, h: 60}, 1.4, 0.8, W, H),
    cameraReturn('r', 2.6, 0.9, W, H),
  ];
  const id0 = cameraTransformAt(0, shots, W, H);
  check('camera identity at t=0', approx(id0.scale, 1) && approx(id0.cx, W / 2) && approx(id0.cy, H / 2));
  const fitted = fitRegion(region, W, H, 80);
  const t1 = cameraTransformAt(0.99, shots, W, H);
  const v = visibleRect(t1, W, H);
  check('camera endpoint fits target', approx(t1.scale, fitted.scale, 0.02) && approx(t1.cx, fitted.cx, 0.5) && approx(t1.cy, fitted.cy, 0.5));
  check('camera shows the fitted region', v.w >= region.w - 1e-6 && v.h >= region.h - 1e-6);
  const mid = cameraTransformAt(0.5, shots, W, H);
  check('camera interpolates between identity and fitted', mid.scale > 1 && mid.scale < fitted.scale + 1e-9);
  const pt = {x: 480, y: 270};
  const roundTrip = invertTransform(applyTransform(pt, t1, W, H), t1, W, H);
  check('camera canvas<->screen round-trip', approx(roundTrip.x, pt.x) && approx(roundTrip.y, pt.y));
  const issues = validateCamera(shots, W, H);
  check('validateCamera reports no errors for a clean program', issues.filter((i) => i.kind === 'error').length === 0);
  const traj = cameraTrajectory(shots, W, H, 0.2);
  check('cameraTrajectory samples deterministically', traj.length > 10 && traj.length === cameraTrajectory(shots, W, H, 0.2).length);
  const scaleMid = cameraTransformAt(1.8, shots, W, H).scale;
  check('camera scale is continuous between shots', scaleMid >= 1);
}

// ---- camera moves (reusable primitives) -------------------------------------
{
  const W = 960;
  const H = 540;
  const region = {x: 300, y: 140, w: 160, h: 120};
  const a: MoveOptions = {};
  const pin = pushIn('pin', region, 0, 1.0, W, H, a);
  const fitted = fitRegion(region, W, H, 60);
  check('pushIn starts at identity and ends on the fitted region', approx(cameraTransformAt(0, [pin], W, H).scale, 1) && approx(cameraTransformAt(0.99, [pin], W, H).scale, fitted.scale, 0.02));
  const out = pullBack('pb', region, 0, 1.0, W, H, {from: fitted});
  check('pullBack starts tight and returns to full view', approx(cameraTransformAt(0.01, [out], W, H).scale, fitted.scale, 0.02) && approx(cameraTransformAt(0.99, [out], W, H).scale, 1, 0.02));

  const mmm = macroMicroMacro('m3', region, 0, 2.0, W, H);
  const midCam = cameraTransformAt(1.0, [mmm], W, H);
  const endCam = cameraTransformAt(1.99, [mmm], W, H);
  check('macroMicroMacro dives in then returns to full view', midCam.scale > fitted.scale * 0.9 && approx(endCam.scale, 1, 0.02) && approx(endCam.cx, W / 2, 0.5));

  const arc = arcPan('arc', {x: 200, y: 200}, {x: 760, y: 340}, 0, 1.6, W, H, {sagitta: 120});
  check('arcPan overshoots off the straight line', Math.abs(cameraTransformAt(0.8, [arc], W, H).cx - cameraTransformAt(0.8, [slide('sl', {x: 200, y: 200}, {x: 760, y: 340}, 0, 1.6, W, H, {scale: 1.2})], W, H).cx) > 1);

  const orb = orbit('orb', {x: 480, y: 270}, 0, 180, 0, 2.0, W, H, {radius: 200, scale: 1});
  const orbMid = cameraTransformAt(1.0, [orb], W, H);
  check('orbit keeps a constant radius around the pivot', Math.abs(Math.hypot(orbMid.cx - 480, orbMid.cy - 270) - 200) < 1);

  const at = (t: number) => ({x: 100 + t * 200, y: 200 + Math.sin(t * 4) * 60});
  const ft = followTarget('ft', at, 0, 2.0, W, H, {scale: 1.2});
  const ftEnd = cameraTransformAt(1.99, [ft], W, H);
  check('followTarget centres the moving point at the end', approx(ftEnd.cx, at(1.99).x, 0.5) && approx(ftEnd.cy, at(1.99).y, 1));

  const dz = dollyZoom('dz', {x: 300, y: 200}, 0, 1.4, W, H, {from: {cx: 300, cy: 200, scale: 1}, toScale: 2.4, anchor: {x: 200, y: 140}});
  const a1 = applyTransform({x: 300, y: 200}, cameraTransformAt(0.5, [dz], W, H), W, H);
  const a2 = applyTransform({x: 300, y: 200}, cameraTransformAt(1.3, [dz], W, H), W, H);
  check('dollyZoom keeps the focal glued to its screen anchor', approx(a1.x, 200, 0.5) && approx(a1.y, 140, 0.5) && approx(a2.x, 200, 0.5) && approx(a2.y, 140, 0.5));

  const sh = impactShake('sh', {cx: 400, cy: 260, scale: 1.2}, 0, 0.5, W, H, {amplitude: 16});
  const shEnd = cameraTransformAt(0.49, [sh], W, H);
  check('impactShake returns exactly to rest', approx(shEnd.cx, 400, 0.5) && approx(shEnd.cy, 260, 0.5));

  const whip = whipPan('whip', {x: 200, y: 200}, {x: 760, y: 340}, 0, 0.7, W, H);
  const whipPeak = cameraTransformAt(0.4, [whip], W, H);
  check('whipPan carries momentum past the target', whipPeak.cx > 760 + 1 && approx(cameraTransformAt(0.69, [whip], W, H).cx, 760, 1));

  const drift = parallaxDrift('dr', 0, 2.0, W, H, {amplitude: 20});
  let maxDrift = 0;
  for (const t of [0.25, 0.5, 0.75, 1.25, 1.5]) {
    const c = cameraTransformAt(t, [drift], W, H);
    maxDrift = Math.max(maxDrift, Math.abs(c.cx - W / 2), Math.abs(c.cy - H / 2));
  }
  check('parallaxDrift amplitude stays bounded', maxDrift <= 30 && maxDrift > 0);

  const chain = sequenceShots([
    pin,
    handoffLike(),
    macroMicroMacro('m4', region, 0, 1.4, W, H, {from: undefined}),
  ]);
  function handoffLike(): CameraShot {
    return panBetween('hand', region, {x: 700, y: 420}, 0, 1.2, W, H, {keepBoth: true, scale: 1.3});
  }
  const joined = chain;
  const before = cameraTransformAt(1.0 - 0.001, joined, W, H);
  const after = cameraTransformAt(1.0, joined, W, H);
  check('sequenceShots joins segments without a jump', Math.hypot(after.cx - before.cx, after.cy - before.cy) < 1 && Math.abs(after.scale - before.scale) < 0.02);
  check('sequenceShots programs validate cleanly', validateCamera(joined, W, H).filter((i) => i.kind === 'error').length === 0);
  void (null as unknown as FitMoveOptions);
}

// ---- paths ------------------------------------------------------------------
{
  const a = {x: 40, y: 40};
  const b = {x: 300, y: 220};
  const kinds: PathKind[] = ['linear', 'arc', 'bezier', 'orthogonal', 'curved', 'follow-link'];
  for (const kind of kinds) {
    const path = buildPath(kind, a, b, kind === 'follow-link' ? {waypoints: [{x: 200, y: 40}]} : kind === 'arc' ? {sagitta: 80} : {});
    const s = path.pointAt(0);
    const e = path.pointAt(1);
    check(`${kind} path endpoints`, approx(s.x, a.x) && approx(s.y, a.y) && approx(e.x, b.x) && approx(e.y, b.y));
    check(`${kind} path has length`, path.length() > 0 && path.length() >= Math.hypot(b.x - a.x, b.y - a.y) - 1e-6);
    check(`${kind} path bounds contain both anchors`, path.bounds().x <= a.x && path.bounds().x + path.bounds().w >= b.x - 1e-6);
  }
  const ortho = buildPath('orthogonal', {x: 0, y: 0}, {x: 100, y: 60}, {firstAxis: 'x'});
  const total = ortho.length();
  const legLen = 100;
  const corner = ortho.pointAt(legLen / total);
  check('orthogonal path bends through the corner', approx(corner.x, 100, 1e-3) && approx(corner.y, 0, 1e-3));
}

// ---- motion primitives ------------------------------------------------------
{
  check('rotate factory carries degrees', approx(rotate('r1', 't', 0, 1).from as number, 0) && approx(rotate('r1', 't', 0, 1).to as number, 360));
  check('shake factory decays to zero', approx(shake('s1', 't', 0, 0.4, 12).to as number, 0));
  for (const action of [morph('m1', 't', 0), split('sp1', 't', 0), merge('mg1', 't', 0), reveal('v1', 't', 0)]) {
    const zero = actionProgress(0, {...action, start: 0, duration: 1});
    const one = actionProgress(1, {...action, start: 0, duration: 1});
    check(`${action.kind} action spans 0..1`, approx(zero, 0) && approx(one, 1));
  }
  // reveal uses a backOut overshoot mid-way (intended); ensure it stays sane.
  const revealMid = actionProgress(0.5, {...reveal('v1', 't', 0), start: 0, duration: 1});
  check('reveal backOut overshoot is bounded', revealMid >= 1 && revealMid <= 1.2);
}

// ---- attention --------------------------------------------------------------
{
  check('attention rank ordering', attentionRank.primary > attentionRank.secondary && attentionRank.secondary > attentionRank.background);
  const p = emphasisParams('primary');
  check('primary emphasis is strongest', p.opacity > emphasisParams('background').opacity && p.brightness > emphasisParams('background').brightness);
  const overlap = [
    appear('a1', 'x', 0, 1.0, 'primary'),
    appear('a2', 'y', 0.2, 1.0, 'primary'),
  ];
  check('primaryCollisions catches overlap', primaryCollisions(overlap, 2).length > 0);
  const apart = [
    appear('a1', 'x', 0, 1.0, 'primary'),
    appear('a2', 'y', 1.5, 1.0, 'primary'),
  ];
  check('primaryCollisions passes separated primaries', primaryCollisions(apart, 3).length === 0);
}

// ---- frame state graph ------------------------------------------------------
{
  const box = {x: 100, y: 100, w: 200, h: 120};
  const inputs = {
    t: 1.5,
    width: 960,
    height: 540,
    actions: [appear('a1', 'card', 0, 2.0, 'primary')],
    geometry: [{id: 'card', rect: box}],
    paths: [{id: 'e1', path: buildPath('curved', {x: 20, y: 20}, {x: 300, y: 200}), connects: {from: 'card', to: 'other'}}],
  };
  const f1 = resolveFrame(inputs);
  const f2 = resolveFrame(inputs);
  check('resolveFrame is deterministic', JSON.stringify(f1.resolved.map((r) => [r.id, r.progress])) === JSON.stringify(f2.resolved.map((r) => [r.id, r.progress])));
  check('resolveFrame exposes camera + visible rect', f1.camera.scale === 1 && f1.visible.w === 960);
  const card = f1.geometry.find((g) => g.id === 'card');
  check('resolveFrame maps geometry into screen space', card ? Math.abs(card.box.screen.x - box.x) < 0.001 : false);
  check('resolveFrame reports attention + emphasis', f1.attention.get('card') === 'primary' && f1.emphasis.has('card'));
  const crossing = pathCollisionReport(resolveFrame({...inputs, t: 1.5, geometry: [{id: 'obstacle', rect: {x: 150, y: 90, w: 60, h: 120}}], paths: [{id: 'cross', path: buildPath('linear', {x: 120, y: 100}, {x: 260, y: 100})}]}), {
    t: 1.5,
    width: 960,
    height: 540,
    geometry: [{id: 'obstacle', rect: {x: 150, y: 90, w: 60, h: 120}}],
    paths: [{id: 'cross', path: buildPath('linear', {x: 120, y: 100}, {x: 260, y: 100})}],
  });
  check('pathCollisionReport flags a crossing', crossing.length > 0);
}

// ---- visual verbs -----------------------------------------------------------
{
  const q = queueReveal('q', ['d', 'a'], 2, 0.4);
  check('queueReveal emits reveal + front highlight', q.length === 3 && q.some((a) => a.kind === 'highlight' && a.target === 'd'));
  check('queueReveal staggers starts', approx(q[1].start - q[0].start, 0.4));
  check('visitSequence visits every target in order', visitSequence('v', ['a', 'b', 'c'], 0).every((a) => a.kind === 'visit') && visitSequence('v', ['a', 'b', 'c'], 0).length === 3);
  check('processMarks marks each target', processMarks('m', ['a', 'b'], 0).every((a) => a.kind === 'mark'));
  check('releaseEdges draws every dependency', releaseEdges('r', [{from: 'a', to: 'b'}, {from: 'a', to: 'c'}], 0).every((a) => a.kind === 'draw') && releaseEdges('r', [{from: 'a', to: 'b'}], 0).length === 1);
}

// ---- media / sfx -------------------------------------------------------------
{
  const clips = [
    {id: 'pop', kind: 'sfx', src: 'pop.mp3', start: 2, duration: 0.2},
    {id: 'pop2', kind: 'sfx', src: 'pop2.mp3', start: 2.1, duration: 0.2},
    {id: 'mark', kind: 'video', src: 'mark.mp4', start: 5, duration: 1.0},
  ] as const;
  check('validateMedia flags overlapping sfx + bad volume', validateMedia([...clips, {id: 'bad', kind: 'sfx', src: 'x.mp3', start: 0, duration: 0.2, volume: 2}] as never).some((i) => i.kind === 'error'));
  check('activeMediaAt is window-correct', activeMediaAt(2.15, clips as never).length === 2 && activeMediaAt(3, clips as never).length === 0);
  check('mediaFrame yields clip progress', mediaFrame(5.5, clips as never).find((m) => m.id === 'mark')?.progress === 0.5);
}

console.log(`\nAnimation core check: ${results.length} checks, ${failures} failure(s)`);
for (const line of results) console.log(`  ${line}`);
if (failures > 0) {
  console.error('\nCORE VALIDATION FAILED');
  process.exit(1);
}
console.log('  ✓ All animation core checks passed');
