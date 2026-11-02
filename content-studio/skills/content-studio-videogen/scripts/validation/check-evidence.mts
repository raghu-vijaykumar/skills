// Evidence Lab's pre-render gate verifies the provenance contract and the
// exact cached originals. It cannot decide whether the research conclusion
// follows from the footage; that remains a human creative/research review.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {parse} from 'yaml';

const target = process.argv[2];
if (!target || !/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(target)) {
  console.error('Usage: npm run check:evidence -- <content-id|video-id>');
  process.exit(1);
}
const videoDir = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', target);
const evidenceStyles = JSON.parse(process.env.VIDEOGEN_EVIDENCE_STYLES ?? '["evidence-lab"]') as string[];
const yamlPath = path.join(videoDir, 'content', 'video.yaml');
let contentId = target;
if (fs.existsSync(yamlPath)) {
  const config = parse(fs.readFileSync(yamlPath, 'utf8')) as {video?: {style?: string}; source?: {contentId?: string}};
  if (!evidenceStyles.includes(config.video?.style ?? '')) {
    console.log(`Evidence: ${target} skipped (style does not require firsthand evidence)`);
    process.exit(0);
  }
  contentId = config.source?.contentId ?? target;
}
if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(contentId)) {
  console.error(`Evidence: invalid source.contentId for ${target}`);
  process.exit(1);
}
const contentDir = path.resolve(process.env.VIDEOGEN_CONTENT_DIR ?? 'content', contentId);
const contentYamlPath = path.join(contentDir, 'content.yaml');
if (!fs.existsSync(contentYamlPath)) {
  console.error(`Evidence: missing shared content package at ${contentYamlPath}`);
  process.exit(1);
}
const config = parse(fs.readFileSync(contentYamlPath, 'utf8')) as {id?: string; style?: string; source?: {assetManifest?: string}};
const issues: string[] = [];
if (config.id !== contentId || !evidenceStyles.includes(config.style ?? '')) issues.push('content.yaml must identify a style requiring firsthand evidence');
const relative = config.source?.assetManifest;
const manifestPath = relative ? path.resolve(contentDir, relative) : '';
if (!relative || !manifestPath.startsWith(`${contentDir}${path.sep}`) || !fs.existsSync(manifestPath)) {
  console.error(`Evidence: ${contentId} requires a local source.assetManifest`);
  process.exit(1);
}
type Entry = {id?: string; file?: string; used?: boolean; usage?: string; attribution?: string; sourceUrl?: string; evidence?: {origin?: string; capturedAt?: string; method?: string; environment?: string; observation?: string; limitation?: string; sha256?: string}};
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as {cacheDir?: string; researchQuestion?: string; assets?: Entry[]};
if (!manifest.researchQuestion?.trim()) issues.push('researchQuestion is required');
if (!Array.isArray(manifest.assets) || !manifest.assets.length) issues.push('at least one captured asset is required');
const cacheDir = path.resolve(manifest.cacheDir ?? '');
const sourceCacheRoot = path.resolve(process.env.VIDEOGEN_SOURCE_CACHE_DIR ?? 'tmp/source-assets');
const expectedCacheDir = path.join(sourceCacheRoot, contentId);
if (cacheDir !== expectedCacheDir) issues.push(`cacheDir must be ${expectedCacheDir}`);
const seen = new Set<string>();
let firsthand = 0;
for (const asset of manifest.assets ?? []) {
  if (asset.used === false) continue;
  const label = asset.id ?? '<missing id>';
  if (!asset.id || seen.has(asset.id)) issues.push(`${label}: missing or duplicate id`);
  seen.add(label);
  if (!asset.usage?.trim()) issues.push(`${label}: usage is required`);
  if (!asset.attribution?.trim()) issues.push(`${label}: attribution is required`);
  const evidence = asset.evidence;
  if (!evidence || !['firsthand', 'source'].includes(evidence.origin ?? '')) issues.push(`${label}: evidence.origin must be firsthand or source`);
  if (evidence?.origin === 'firsthand') firsthand++;
  if (evidence?.origin === 'source' && !asset.sourceUrl?.trim()) issues.push(`${label}: source media requires sourceUrl`);
  for (const key of ['capturedAt', 'method', 'environment', 'observation', 'limitation', 'sha256'] as const) {
    if (!evidence?.[key]?.trim()) issues.push(`${label}: evidence.${key} is required`);
  }
  if (evidence?.capturedAt && (!/^\d{4}-\d{2}-\d{2}(T.*)?$/.test(evidence.capturedAt) || Number.isNaN(Date.parse(evidence.capturedAt)))) issues.push(`${label}: capturedAt is invalid`);
  if (evidence?.sha256 && !/^[0-9a-f]{64}$/.test(evidence.sha256)) issues.push(`${label}: sha256 must be 64 lowercase hex characters`);
  if (!asset.file || path.basename(asset.file) !== asset.file) {
    issues.push(`${label}: file must be a single cache filename`);
    continue;
  }
  const file = path.join(expectedCacheDir, asset.file);
  if (!fs.existsSync(file)) {
    issues.push(`${label}: cached original missing at ${file}`);
    continue;
  }
  const actual = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  if (actual !== evidence?.sha256) issues.push(`${label}: cached original differs from manifest sha256`);
}
if (firsthand === 0) issues.push('at least one used firsthand capture is required');
if (issues.length) {
  console.error(`Evidence: ${contentId} failed (${issues.length} issue${issues.length === 1 ? '' : 's'})`);
  for (const issue of issues) console.error(`  - ${issue}`);
  process.exit(1);
}
console.log(`Evidence: ${contentId} verified ${seen.size} used asset(s), ${firsthand} firsthand capture(s)`);
