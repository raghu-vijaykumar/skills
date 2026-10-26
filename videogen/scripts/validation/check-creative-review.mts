// Evidence-record gate for a visual creative review. This validates that a
// complete review was performed against captured output; it cannot judge
// aesthetics or truthfulness in place of a vision-capable reviewer.
import * as fs from 'node:fs';
import * as path from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {parse} from 'yaml';

type Range = {startSeconds: number; endSeconds: number; file: string};
type VisualObservation = {range?: Range; startSeconds?: number; endSeconds?: number; frames?: string[]; visibleEvidence: string; motionEvidence: string; phoneReadability: string; issueCheck: string};
type ElementReview = {id: string; status: string; representation: string; sourceComponent: string; componentExport: string; sourceSha256: string; referenceSource: string; isolatedRender: string; integratedFrame: string; identityEvidence: string; structureEvidence: string; styleEvidence: string; adoptionReason: string; defects: string[]};
type HeroShot = {id: string; name: string; soloRange?: Range; soloFrames?: string[]; soloAssessment: string; integrationVerification: string; framingIntent: string; beforeFrame: string; afterFrame: string; framingVerification: string; range?: Range; integratedFrames?: string[]; visualEvent: string; teachingPayoff: string; mechanismAccuracy: string; distinctFromOtherHeroes: string};
type Transition = {from: string; to: string; kind: string; range?: Range; beforeFrame?: string; afterFrame?: string; persistentSubject: string; observedEffect: string};
type Review = {
  videoId: string;
  status: string;
  reviewMode?: 'render' | 'studio';
  storyboard: {beat: string; visualForm: string; representationReason: string}[];
  visualVarietyReview: {status: string; formFrames: {visualForm: string; file: string}[]; observedBenefit: string; retainedFormReason?: string};
  finalRender?: {runtimeSeconds: number; ranges: Range[]};
  studioReview?: {runtimeSeconds: number; frames: {timeSeconds: number; file: string}[]; playbackReviewed: boolean; playbackEvidence: string};
  scores: Record<string, number>;
  heroShots: HeroShot[];
  transitions: Transition[];
  phoneSizeReview: {focalSubjectClear: boolean; essentialValuesLegible: boolean};
  renderedReview: {status: string; method: string; reviewer: string; contactSheet: string; reviewedResolution: string; categoryEvidence: Record<string, string>; observations: VisualObservation[]};
  elementReviews: {required: string[]; reviews: ElementReview[]};
  reviewNotes: {strengths: string[]; defects: string[]; fixesApplied: string[]};
};

const videoId = process.argv[2];
if (!videoId) {
  console.error('Usage: npm run check:creative -- <video-id>');
  process.exit(1);
}

const root = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId);
const reviewPath = path.join(root, 'research', 'creative-review.yaml');
const narrationPath = path.join(root, 'assets', 'generated', 'narration.ts');
const narrationSourcePath = path.join(root, 'content', 'narration.yaml');
const metadataPath = path.join(root, 'content', 'video.yaml');
const issues: string[] = [];
if (!fs.existsSync(root)) issues.push(`video directory does not exist: videos/${videoId}`);
if (!fs.existsSync(reviewPath)) issues.push(`missing rendered review record: ${path.relative(process.cwd(), reviewPath)}`);
if (fs.existsSync(narrationSourcePath) && !fs.existsSync(narrationPath)) issues.push(`missing generated narration cues: ${path.relative(process.cwd(), narrationPath)}`);
if (!fs.existsSync(narrationSourcePath) && !fs.existsSync(metadataPath)) issues.push(`missing duration metadata: ${path.relative(process.cwd(), metadataPath)}`);
if (issues.length) {
  for (const issue of issues) console.error(`✗ ${issue}`);
  process.exit(1);
}

const readRuntime = (): number | null => {
  // Music-only identities have no spoken cues; their declared duration is the
  // stable review clock. Ignore stale generated narration from earlier edits.
  if (!fs.existsSync(narrationSourcePath)) {
    const metadata = parse(fs.readFileSync(metadataPath, 'utf8')) as {video?: {durationSeconds?: number}};
    const seconds = Number(metadata?.video?.durationSeconds);
    return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
  }
  const src = fs.readFileSync(narrationPath, 'utf8');
  const match = src.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
  if (!match) return null;
  try {
    const cues = JSON.parse(match[1]) as {endSeconds?: number}[];
    const end = Number(cues[cues.length - 1]?.endSeconds);
    return Number.isFinite(end) && end > 0 ? end : null;
  } catch {
    return null;
  }
};

function failIf(condition: boolean, message: string): void {
  if (condition) issues.push(message);
}

function noPlaceholder(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0 && !/\b(todo|tbd|pending|unreviewed|fill me|example text)\b/i.test(value);
}

function checkedRange(range: Range | undefined, label: string): void {
  if (!range || !Number.isFinite(range.startSeconds) || !Number.isFinite(range.endSeconds) || range.endSeconds <= range.startSeconds) {
    issues.push(`${label}: invalid render range`);
    return;
  }
  if (!noPlaceholder(range.file)) {
    issues.push(`${label}: render file path is missing or a placeholder`);
    return;
  }
  const file = path.resolve(root, range.file);
  const relative = path.relative(root, file);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    issues.push(`${label}: render path must remain inside videos/${videoId}`);
    return;
  }
  if (!fs.existsSync(file)) {
    issues.push(`${label}: render file does not exist (${path.relative(process.cwd(), file)})`);
    return;
  }
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file], {encoding: 'utf8'});
  if (probe.error || probe.status !== 0) {
    issues.push(`${label}: ffprobe could not read the cited render`);
    return;
  }
  const duration = Number(probe.stdout.trim());
  const expected = range.endSeconds - range.startSeconds;
  if (!Number.isFinite(duration) || Math.abs(duration - expected) > 0.6) {
    issues.push(`${label}: render duration ${duration.toFixed(2)}s does not match reviewed range ${expected.toFixed(2)}s`);
  }
}

function checkedVideoLocalFile(filePath: string | undefined, label: string, extensions: string[], boundary = root): string | null {
  if (!noPlaceholder(filePath)) {
    issues.push(`${label}: file path is missing or a placeholder`);
    return null;
  }
  const file = path.resolve(root, filePath);
  const relative = path.relative(boundary, file);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    issues.push(`${label}: path must remain inside ${boundary === root ? `videos/${videoId}` : 'the workspace'}`);
    return null;
  }
  if (!extensions.includes(path.extname(file).toLowerCase())) { issues.push(`${label}: unsupported file type`); return null; }
  if (!fs.existsSync(file)) { issues.push(`${label}: file does not exist (${path.relative(process.cwd(), file)})`); return null; }
  return file;
}

let review: Review | null = null;
try {
  review = parse(fs.readFileSync(reviewPath, 'utf8')) as Review;
} catch (error) {
  issues.push(`could not parse ${path.relative(process.cwd(), reviewPath)}: ${error instanceof Error ? error.message : String(error)}`);
}

const runtime = readRuntime();
failIf(runtime === null, 'narration cues or music-only duration metadata are invalid');
if (review && runtime !== null) {
  const studioMode = review.reviewMode === 'studio';
  failIf(review.videoId !== videoId, `review videoId must equal ${videoId}`);
  failIf(review.status !== 'pass', 'status must be "pass" after all creative issues are fixed and recaptured');
  failIf(Boolean(review.reviewMode && !['render','studio'].includes(review.reviewMode)), 'reviewMode must be render or studio');
  if (studioMode) {
    const studio = review.studioReview;
    failIf(!Number.isFinite(studio?.runtimeSeconds) || Math.abs((studio?.runtimeSeconds ?? 0) - runtime) > 0.6, `studioReview.runtimeSeconds must match narration runtime ${runtime.toFixed(2)}s`);
    failIf(studio?.playbackReviewed !== true || !noPlaceholder(studio?.playbackEvidence) || (studio?.playbackEvidence?.length ?? 0) < 60, 'studioReview must describe inspected motion and narration playback');
    const frames = Array.isArray(studio?.frames) ? studio.frames : [];
    failIf(frames.length < Math.ceil(runtime / 3), 'studioReview.frames must sample the full runtime at most every three seconds');
    failIf(new Set(frames.map(frame=>frame.file)).size !== frames.length, 'studioReview.frames must cite distinct captures');
    const orderedFrames = [...frames].sort((a,b)=>a.timeSeconds-b.timeSeconds);
    failIf((orderedFrames[0]?.timeSeconds ?? Infinity) > 0.1, 'studioReview.frames must include the opening frame');
    for (let i=0;i<orderedFrames.length;i++) {
      const frame=orderedFrames[i];
      failIf(!Number.isFinite(frame.timeSeconds) || frame.timeSeconds<0 || frame.timeSeconds>runtime, `studioReview.frames[${i}] has invalid time`);
      checkedVideoLocalFile(frame.file, `studioReview.frames[${i}]`, ['.png','.jpg','.jpeg','.webp']);
      if(i>0) failIf(frame.timeSeconds-orderedFrames[i-1].timeSeconds>3.1, `studioReview.frames has a gap longer than three seconds before ${frame.timeSeconds}s`);
    }
    failIf((orderedFrames.at(-1)?.timeSeconds ?? 0) < runtime-3.1, 'studioReview.frames must reach the conclusion');
  } else {
    failIf(!Number.isFinite(review.finalRender?.runtimeSeconds) || Math.abs((review.finalRender?.runtimeSeconds ?? 0) - runtime) > 0.6, `finalRender.runtimeSeconds must match narration runtime ${runtime.toFixed(2)}s`);
    failIf(!Array.isArray(review.finalRender?.ranges) || review.finalRender.ranges.length === 0, 'finalRender.ranges must cite the actual rendered review clips');
    const ranges = Array.isArray(review.finalRender?.ranges) ? review.finalRender.ranges : [];
    for (let i = 0; i < ranges.length; i += 1) checkedRange(ranges[i], `finalRender.ranges[${i}]`);
    const ordered = [...ranges].sort((a, b) => a.startSeconds - b.startSeconds);
    let coveredTo = 0;
    for (const range of ordered) {
      if (range.startSeconds > coveredTo + 0.1) issues.push(`render review has an uninspected gap from ${coveredTo.toFixed(2)}s to ${range.startSeconds.toFixed(2)}s`);
      coveredTo = Math.max(coveredTo, range.endSeconds);
    }
    failIf(coveredTo < runtime - 0.6, `reviewed render ranges end at ${coveredTo.toFixed(2)}s; full runtime is ${runtime.toFixed(2)}s`);
  }

  const scores = review.scores ?? {};
  const requiredScores = ['hook', 'story', 'motion', 'continuity', 'composition', 'distinctiveness', 'technicalAccuracy', 'finish'];
  for (const category of requiredScores) {
    const score = scores[category];
    failIf(!Number.isInteger(score) || score < 0 || score > 2, `scores.${category} must be 0, 1, or 2`);
    failIf(score !== 2, `scores.${category} is ${String(score)}; a 2 is required to pass`);
  }

  const heroes = Array.isArray(review.heroShots) ? review.heroShots : [];
  // Force a representation decision for each beat, then tie that decision to
  // actual distinct images. No arbitrary scene-change quota replaces judgment.
  const beats = Array.isArray(review.storyboard) ? review.storyboard : [];
  failIf(beats.length === 0, 'storyboard must record visualization choices before implementation');
  const forms = new Set(['physical-process','mathematical-plot','code-execution','data-visualization','spatial-model','symbolic-transform','real-world-object']);
  for (const beat of beats) {
    failIf(!forms.has(beat.visualForm), `storyboard.${beat.beat ?? '?'}: visualForm must identify an accurate representation`);
    failIf(!noPlaceholder(beat.representationReason) || beat.representationReason.trim().length < 45, `storyboard.${beat.beat ?? '?'}: representationReason must explain why this form teaches the beat`);
  }
  const chosenForms = [...new Set(beats.map(beat=>beat.visualForm))];
  const variety = review.visualVarietyReview;
  failIf(variety?.status !== 'pass', 'visualVarietyReview.status must be pass after rendered representation review');
  failIf(!noPlaceholder(variety?.observedBenefit) || variety.observedBenefit.trim().length < 60, 'visualVarietyReview.observedBenefit must describe the rendered teaching benefit');
  if (chosenForms.length === 1) failIf(!noPlaceholder(variety?.retainedFormReason) || (variety.retainedFormReason?.trim().length ?? 0) < 60, 'a retained single visual form requires an inspected teaching rationale');
  const formFrames = Array.isArray(variety?.formFrames) ? variety.formFrames : [];
  for (const form of chosenForms) failIf(!formFrames.some(item=>item.visualForm===form), `visualVarietyReview: missing representative rendered frame for ${form}`);
  failIf(new Set(formFrames.map(item=>item.file)).size !== formFrames.length, 'visualVarietyReview: different forms must cite distinct rendered frames');
  for (const item of formFrames) checkedVideoLocalFile(item.file, `visualVarietyReview.${item.visualForm}`, ['.png','.jpg','.jpeg','.webp']);
  failIf(heroes.length < 2, 'at least two distinct, inspected hero shots are required');
  for (const hero of heroes) {
    for (const field of ['id', 'name', 'visualEvent', 'teachingPayoff', 'mechanismAccuracy', 'distinctFromOtherHeroes'] as const) {
      failIf(!noPlaceholder(hero[field]), `heroShots.${hero.id ?? '?'}: ${field} must contain reviewed evidence`);
    }
    // A beautiful still cannot approve an unreviewed transition or its final
    // camera/caption context. Require real moving evidence at both stages.
    if (studioMode && !hero.soloRange) {
      failIf((hero.soloFrames?.length ?? 0) < 2, `heroShots.${hero.id ?? '?'} needs at least two solo frames`);
      for (const file of hero.soloFrames ?? []) checkedVideoLocalFile(file, `heroShots.${hero.id ?? '?'}.soloFrames`, ['.png','.jpg','.jpeg','.webp']);
    } else checkedRange(hero.soloRange, `heroShots.${hero.id ?? '?'}.soloRange`);
    failIf(Boolean(hero.soloRange?.file && hero.range?.file) && path.resolve(root,hero.soloRange.file) === path.resolve(root,hero.range.file), `heroShots.${hero.id ?? '?'}: solo and integrated evidence must be distinct renders`);
    for (const field of ['soloAssessment', 'integrationVerification', 'framingIntent', 'framingVerification'] as const) {
      failIf(!noPlaceholder(hero[field]) || hero[field].trim().length < 45, `heroShots.${hero.id ?? '?'}.${field} must describe inspected solo and integrated behavior`);
    }
    checkedVideoLocalFile(hero.beforeFrame, `heroShots.${hero.id ?? '?'}.beforeFrame`, ['.png','.jpg','.jpeg','.webp']);
    checkedVideoLocalFile(hero.afterFrame, `heroShots.${hero.id ?? '?'}.afterFrame`, ['.png','.jpg','.jpeg','.webp']);
    failIf(Boolean(hero.beforeFrame && hero.afterFrame) && path.resolve(root,hero.beforeFrame) === path.resolve(root,hero.afterFrame), `heroShots.${hero.id ?? '?'}: framing review needs distinct before and after frames`);
    if (studioMode && !hero.range) {
      failIf((hero.integratedFrames?.length ?? 0) < 3, `heroShots.${hero.id ?? '?'} needs at least three integrated frames`);
      for (const file of hero.integratedFrames ?? []) checkedVideoLocalFile(file, `heroShots.${hero.id ?? '?'}.integratedFrames`, ['.png','.jpg','.jpeg','.webp']);
    } else checkedRange(hero.range, `heroShots.${hero.id ?? '?'}`);
  }
  const heroIds = heroes.map((hero) => hero.id);
  failIf(new Set(heroIds).size !== heroIds.length, 'hero shot ids must be unique');

  const transitions = Array.isArray(review.transitions) ? review.transitions : [];
  failIf(transitions.length < 2, 'at least two major scene-boundary transitions must be reviewed');
  const allowedKinds = new Set(['transformation', 'object-handoff', 'camera-travel', 'spatial-continuity', 'deliberate-cut']);
  for (const transition of transitions) {
    failIf(!noPlaceholder(transition.from) || !noPlaceholder(transition.to), 'each transition must name its source and destination beats');
    failIf(!allowedKinds.has(transition.kind), `transition ${transition.from ?? '?'} → ${transition.to ?? '?'} has an unsupported kind`);
    failIf(!noPlaceholder(transition.persistentSubject) || !noPlaceholder(transition.observedEffect), `transition ${transition.from ?? '?'} → ${transition.to ?? '?'} must say what persists and what the viewer sees`);
    if (studioMode && !transition.range) {
      checkedVideoLocalFile(transition.beforeFrame, `transition ${transition.from ?? '?'}.beforeFrame`, ['.png','.jpg','.jpeg','.webp']);
      checkedVideoLocalFile(transition.afterFrame, `transition ${transition.to ?? '?'}.afterFrame`, ['.png','.jpg','.jpeg','.webp']);
      failIf(Boolean(transition.beforeFrame && transition.beforeFrame===transition.afterFrame), `transition ${transition.from ?? '?'} needs distinct before and after frames`);
    } else checkedRange(transition.range, `transition ${transition.from ?? '?'} → ${transition.to ?? '?'}`);
  }

  failIf(review.phoneSizeReview?.focalSubjectClear !== true, 'phoneSizeReview.focalSubjectClear must be true');
  failIf(review.phoneSizeReview?.essentialValuesLegible !== true, 'phoneSizeReview.essentialValuesLegible must be true');

  // Scores and authored hero-shot descriptions are claims. Require a separate
  // visual review record tied to actual timecoded frame or clip evidence.
  const rendered = review.renderedReview;
  failIf(rendered?.status !== 'pass', 'renderedReview.status must be "pass" after visual defects are fixed');
  failIf(rendered?.method !== 'vision', 'renderedReview.method must be "vision"; source-only or geometry-only checks do not qualify');
  failIf(!noPlaceholder(rendered?.reviewer), 'renderedReview.reviewer must identify the vision-capable reviewer');
  failIf(!/^\d{3,4}x\d{3,4}$/.test(rendered?.reviewedResolution ?? ''), 'renderedReview.reviewedResolution must record the inspected image size (for example 540x960)');
  checkedVideoLocalFile(rendered?.contactSheet, 'renderedReview.contactSheet', ['.png', '.jpg', '.jpeg', '.webp']);
  const categoryEvidence = rendered?.categoryEvidence ?? {};
  for (const category of requiredScores) {
    const evidence = categoryEvidence[category];
    failIf(!noPlaceholder(evidence) || evidence.trim().length < 45, `renderedReview.categoryEvidence.${category} must describe visible evidence from the reviewed output`);
  }
  const observations = Array.isArray(rendered?.observations) ? rendered.observations : [];
  failIf(observations.length < 3, 'renderedReview.observations must record at least three time-coded visual inspections');
  for (let i = 0; i < observations.length; i += 1) {
    const observation = observations[i];
    const label = `renderedReview.observations[${i}]`;
    if (studioMode && !observation.range) {
      failIf(!Number.isFinite(observation.startSeconds) || !Number.isFinite(observation.endSeconds) || (observation.endSeconds ?? 0) <= (observation.startSeconds ?? 0), `${label} has invalid time bounds`);
      failIf((observation.frames?.length ?? 0) < 3, `${label} needs at least three reviewed frames`);
      for (const file of observation.frames ?? []) checkedVideoLocalFile(file, `${label}.frames`, ['.png','.jpg','.jpeg','.webp']);
    } else checkedRange(observation.range, label);
    for (const field of ['visibleEvidence', 'motionEvidence', 'phoneReadability', 'issueCheck'] as const) {
      failIf(!noPlaceholder(observation[field]) || observation[field].trim().length < 24, `${label}.${field} must record a concrete rendered observation`);
    }
  }
  const bounds=(observation:VisualObservation)=>observation.range ?? {startSeconds:observation.startSeconds ?? NaN,endSeconds:observation.endSeconds ?? NaN,file:''};
  const reviewedObservations = observations.filter((observation) => Number.isFinite(bounds(observation).startSeconds) && Number.isFinite(bounds(observation).endSeconds)).sort((a, b) => bounds(a).startSeconds - bounds(b).startSeconds);
  let observedTo = 0;
  for (const observation of reviewedObservations) {
    const span=bounds(observation);
    if (span.startSeconds > observedTo + 0.1) issues.push(`visual observations have an uninspected gap from ${observedTo.toFixed(2)}s to ${span.startSeconds.toFixed(2)}s`);
    observedTo = Math.max(observedTo, span.endSeconds);
  }
  failIf(observedTo < runtime - 0.6, `visual observations end at ${observedTo.toFixed(2)}s; full runtime is ${runtime.toFixed(2)}s`);

  // Literal subjects must resemble their references before adoption. Internal
  // mechanism abstractions are reviewed as schematics, with placement and
  // meaning recorded explicitly rather than pretending to be exact teardowns.
  const requiredElements = Array.isArray(review.elementReviews?.required) ? review.elementReviews.required : [];
  const elements = Array.isArray(review.elementReviews?.reviews) ? review.elementReviews.reviews : [];
  failIf(requiredElements.length < 2 || !requiredElements.every(noPlaceholder), 'elementReviews.required must name every major subject and teaching element (at least two)');
  failIf(new Set(requiredElements).size !== requiredElements.length, 'elementReviews.required ids must be unique');
  const reviewedElementIds = elements.map((element) => element.id);
  failIf(new Set(reviewedElementIds).size !== reviewedElementIds.length, 'element review ids must be unique');
  for (const id of requiredElements) failIf(!reviewedElementIds.includes(id), `elementReviews: missing isolated and integrated visual assessment for ${id}`);
  const isolatedRenders = elements.map((element) => element.isolatedRender);
  failIf(new Set(isolatedRenders).size !== isolatedRenders.length, 'each element must cite its own isolated preview, not reuse a whole-scene image');
  for (const element of elements) {
    const label = `elementReviews.${element.id ?? '?'}`;
    failIf(!requiredElements.includes(element.id), `${label}: not listed in required elements`);
    failIf(element.status !== 'pass', `${label}: unresolved visual quality or resemblance issue`);
    failIf(!['literal', 'schematic'].includes(element.representation), `${label}.representation must be literal or schematic`);
    failIf(!noPlaceholder(element.referenceSource), `${label}.referenceSource must identify the actual subject or mechanism reference`);
    const sourceFile = checkedVideoLocalFile(element.sourceComponent, `${label}.sourceComponent`, ['.tsx', '.ts'], process.cwd());
    failIf(!noPlaceholder(element.componentExport), `${label}.componentExport must identify the reviewed component`);
    if (sourceFile) {
      const source = fs.readFileSync(sourceFile, 'utf8');
      failIf(!source.includes(`function ${element.componentExport}(`) && !source.includes(`const ${element.componentExport} `), `${label}: named component is not present in the cited source`);
      // Changing an accepted subject invalidates its review until the actual
      // component has been rendered and inspected again.
      const sourceHash = createHash('sha256').update(fs.readFileSync(sourceFile)).digest('hex');
      failIf(element.sourceSha256 !== sourceHash, `${label}: source changed since visual acceptance; re-render and re-review this element`);
    }
    checkedVideoLocalFile(element.isolatedRender, `${label}.isolatedRender`, ['.png', '.jpg', '.jpeg', '.webp']);
    checkedVideoLocalFile(element.integratedFrame, `${label}.integratedFrame`, ['.png', '.jpg', '.jpeg', '.webp']);
    for (const field of ['identityEvidence', 'structureEvidence', 'styleEvidence', 'adoptionReason'] as const) {
      failIf(!noPlaceholder(element[field]) || element[field].trim().length < 45, `${label}.${field} must record the visual assessment before adoption`);
    }
    failIf(!Array.isArray(element.defects) || element.defects.length > 0, `${label}.defects must be an empty completed list after all issues are fixed`);
  }
  failIf(!Array.isArray(review.reviewNotes?.strengths) || review.reviewNotes.strengths.length === 0 || !review.reviewNotes.strengths.every(noPlaceholder), 'reviewNotes.strengths must record what works in the render');
  failIf(!Array.isArray(review.reviewNotes?.defects) || !review.reviewNotes.defects.every(noPlaceholder), 'reviewNotes.defects must be a completed list, empty only when no defects remain');
  failIf(review.reviewNotes?.defects?.length > 0, 'reviewNotes.defects is not empty; fix them, re-render, and review again');
  failIf(!Array.isArray(review.reviewNotes?.fixesApplied) || !review.reviewNotes.fixesApplied.every(noPlaceholder), 'reviewNotes.fixesApplied must be a completed list');
}

if (issues.length) {
  console.error(`\nCreative review gate: ${videoId} — FAIL (${issues.length} issue${issues.length === 1 ? '' : 's'})`);
  for (const issue of issues) console.error(`  ✗ ${issue}`);
  process.exit(1);
}

console.log(`Creative review gate: ${videoId} — PASS`);
console.log('  timecoded visual evidence, phone-size observations, and individual element assessments are complete');
console.log('  machine checks enforce evidence completeness; the vision review owns the aesthetic judgment');
