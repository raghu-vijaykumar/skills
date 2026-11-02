import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

const video = process.argv[2];
if (!video) {
  console.error('Usage: videogen narration <video-id>');
  process.exit(1);
}

// The caller resolves the configured video directory before invoking this script.
const root = path.resolve(video);
const yamlFile = path.join(root, 'content', 'video.yaml');
const outDir = path.join(root, 'assets', 'generated', 'audio');
const out = path.join(outDir, 'narration.mp3');
const generatedNarration = path.join(root, 'assets', 'generated', 'narration.ts');
const cacheFile = path.join(outDir, '.narration-cache.json');
const MAX_WORDS_PER_PHRASE = 10;
const CACHE_VERSION = 4;

if (!fs.existsSync(yamlFile)) {
  console.error(`Video YAML not found: ${yamlFile}`);
  process.exit(1);
}

const videoSource = fs.readFileSync(yamlFile, 'utf8').replace(/\r/g, '');
const narrationPath = videoSource.split('\n')
  .map((line) => line.trim())
  .map((line) => line.match(/^narration:\s+(.+)$/)?.[1])
  .find((value) => value && !value.startsWith('{') && !value.startsWith('['));

const narrationFile = narrationPath
  ? path.resolve(root, 'content', narrationPath.replace(/^['"]|['"]$/g, ''))
  : null;

if (!narrationFile || !fs.existsSync(narrationFile)) {
  console.error(`Narration YAML not found: ${narrationFile || path.join(root, 'content', 'narration.yaml')}`);
  process.exit(1);
}

const narrationSource = fs.readFileSync(narrationFile, 'utf8').replace(/\r/g, '');
const narrationLines = narrationSource.split('\n');
const phrases = [];
let inPhrases = false;
let maxWords = MAX_WORDS_PER_PHRASE;
let voice = 'en-US-GuyNeural';
let globalRate = null;
let targetWpm = null;
// Default narration pace for videos without an explicit rate/wpm.
const DEFAULT_WPM = 150;

const unquote = (value) => {
  const trimmed = value.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1).replace(/\\"/g, '"').replace(/\\'/g, "'");
  }
  return trimmed;
};

const parseInlinePhrase = (value) => {
  const body = value.trim().replace(/^-\s*\{/, '').replace(/\}\s*$/, '');
  const phrase = {};
  const fields = [];
  let current = '';
  let quote = null;
  let escaped = false;
  let depth = 0;

  for (const char of body) {
    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }
    if (quote && char === '\\') {
      current += char;
      escaped = true;
      continue;
    }
    if ((char === '"' || char === "'") && (!quote || quote === char)) {
      quote = quote ? null : char;
      current += char;
      continue;
    }
    if (!quote && char === '{') depth += 1;
    if (!quote && char === '}') depth -= 1;
    if (!quote && char === ',' && depth === 0) {
      fields.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  if (current.trim()) fields.push(current);

  for (const field of fields) {
    const separator = field.indexOf(':');
    if (separator < 0) continue;
    const key = field.slice(0, separator).trim();
    const valuePart = field.slice(separator + 1).trim();
    if (key === 'id') phrase.id = unquote(valuePart);
    else if (key === 'text') phrase.text = unquote(valuePart);
    else if (key === 'rate') phrase.rate = unquote(valuePart);
    else if (key === 'pause') phrase.pause = Number(unquote(valuePart));
  }
  return phrase;
};

for (const raw of narrationLines) {
  const trimmed = raw.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;

  if (/^phrases:\s*$/.test(trimmed)) {
    inPhrases = true;
    continue;
  }

  if (!inPhrases) {
    if (/^voice:\s*/.test(trimmed)) voice = unquote(trimmed.replace(/^voice:\s*/, ''));
    if (/^max_words_per_phrase:\s*/.test(trimmed)) maxWords = Number(trimmed.replace(/^max_words_per_phrase:\s*/, ''));
    if (/^rate:\s*/.test(trimmed)) globalRate = unquote(trimmed.replace(/^rate:\s*/, '')) || null;
    if (/^wpm:\s*/.test(trimmed)) targetWpm = Number(unquote(trimmed.replace(/^wpm:\s*/, ''))) || null;
    continue;
  }

  if (/^-\s*\{.*\}\s*$/.test(trimmed)) {
    phrases.push(parseInlinePhrase(trimmed));
    continue;
  }

  if (/^-\s+id:\s*/.test(trimmed)) {
    phrases.push({id: unquote(trimmed.replace(/^-\s+id:\s*/, ''))});
    continue;
  }

  const current = phrases[phrases.length - 1];
  if (!current) continue;
  if (/^text:\s*/.test(trimmed)) current.text = unquote(trimmed.replace(/^text:\s*/, ''));
}

const errors = [];
if (phrases.length === 0) errors.push('narration.phrases is empty or missing.');
if (!Number.isInteger(maxWords) || maxWords < 1) errors.push('narration.max_words_per_phrase must be a positive integer.');

const seenIds = new Set();
for (const phrase of phrases) {
  if (!phrase.id) errors.push('[?] phrase id is missing.');
  if (!phrase.text || !phrase.text.trim()) errors.push(`[${phrase.id ?? '?'}] narration text is empty.`);
  phrase.text = (phrase.text || '').replace(/\s+/g, ' ').trim();
  phrase.wordCount = phrase.text ? phrase.text.split(/\s+/).filter(Boolean).length : 0;
  if (phrase.wordCount > maxWords) errors.push(`[${phrase.id ?? '?'}] ${phrase.wordCount} words; maximum is ${maxWords}. Split this phrase.`);
  if (seenIds.has(phrase.id)) errors.push(`[${phrase.id}] duplicate phrase id.`);
  seenIds.add(phrase.id);
}

if (errors.length > 0) {
  console.error('\nNARRATION VALIDATION FAILED');
  for (const error of errors) console.error(`  ✗ ${error}`);
  process.exit(1);
}

fs.mkdirSync(outDir, {recursive: true});

const cachePayload = JSON.stringify({version: CACHE_VERSION, source: narrationSource, voice, maxWords, globalRate, targetWpm});
const cacheKey = crypto.createHash('sha256').update(cachePayload).digest('hex');

let cache = null;
if (fs.existsSync(cacheFile)) {
  try {
    cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
  } catch {
    cache = null;
  }
}

const cacheHit = cache?.version === CACHE_VERSION
  && cache?.key === cacheKey
  && fs.existsSync(out)
  && Array.isArray(cache?.timedPhrases)
  && cache.timedPhrases.length === phrases.length
  && cache.timedPhrases.every((phrase) => Number.isFinite(phrase.startSeconds) && Number.isFinite(phrase.endSeconds));

if (cacheHit) {
  fs.writeFileSync(generatedNarration, `// GENERATED FILE. DO NOT EDIT.\nexport const narrationCues = ${JSON.stringify(cache.timedPhrases, null, 2)} as const;\n`);
  process.exit(0);
}

const tempDir = path.join(outDir, '.phrases');
fs.rmSync(tempDir, {recursive: true, force: true});
fs.mkdirSync(tempDir, {recursive: true});

const python = process.platform === 'win32' ? 'python' : 'python3';
const generated = [];
const phraseFile = (i) => path.join(tempDir, `${String(i).padStart(4, '0')}.mp3`);

function synthesize(rateArg) {
  for (let i = 0; i < phrases.length; i += 1) {
    const ttsArgs = ['-m', 'edge_tts', '--voice', voice, '--text', phrases[i].text, '--write-media', phraseFile(i)];
    const rate = phrases[i].rate || rateArg;
    if (rate) ttsArgs.push(`--rate=${rate}`);
    // The remote voice service occasionally drops one phrase mid-build; retry
    // that phrase so a transient socket failure does not discard the full film.
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        execFileSync(python, ttsArgs, {stdio: ['ignore', 'ignore', 'pipe']});
        break;
      } catch (error) {
        if (attempt === 3) throw error;
        console.log(`Retrying narration phrase ${i + 1}/${phrases.length} (attempt ${attempt + 1}).`);
      }
    }
  }
}

function applyPauses() {
  for (let i = 0; i < phrases.length; i += 1) {
    if (Number.isFinite(phrases[i].pause) && phrases[i].pause > 0) {
      const padded = path.join(tempDir, `${String(i).padStart(4, '0')}-padded.mp3`);
      execFileSync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', phraseFile(i), '-af', `apad=pad_dur=${phrases[i].pause}`, '-c:a', 'libmp3lame', '-q:a', '4', padded], {stdio: ['ignore', 'ignore', 'pipe']});
      fs.renameSync(padded, phraseFile(i));
    }
    generated[i] = phraseFile(i);
  }
}

const probeDuration = (file) => {
  try {
    const duration = Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']}).trim());
    if (!Number.isFinite(duration) || duration <= 0) throw new Error('invalid duration');
    return duration;
  } catch (error) {
    console.error(`\nUnable to read audio duration for ${file}.`);
    if (error?.stderr) console.error(String(error.stderr).trim());
    process.exit(1);
  }
};

const totalWords = phrases.reduce((sum, phrase) => sum + (phrase.wordCount || 0), 0);
let appliedRate = globalRate;
let audioDurations = [];
try {
  synthesize(globalRate);
  applyPauses();
  audioDurations = generated.map(probeDuration);
  if (!globalRate) {
    // No explicit rate: retarget to the video's WPM goal (default 150) so all
    // videos share the same narration pace.
    const target = targetWpm || DEFAULT_WPM;
    const total = audioDurations.reduce((sum, d) => sum + d, 0);
    const current = (totalWords / total) * 60;
    const pct = Math.round((target / current - 1) * 100);
    if (Math.abs(pct) > 1) {
      appliedRate = `${pct > 0 ? '+' : ''}${pct}%`;
      console.log(`Retargeting narration to ~${target} WPM (measured ${current.toFixed(1)} at default rate): using rate ${appliedRate}.`);
      synthesize(appliedRate);
      applyPauses();
      audioDurations = generated.map(probeDuration);
    }
    const finalWpm = (totalWords / audioDurations.reduce((sum, d) => sum + d, 0)) * 60;
    console.log(`Narration pace: ${totalWords} words, ${finalWpm.toFixed(1)} WPM.`);
  }
} catch (error) {
  console.error('\nUnable to generate narration with Python edge-tts.');
  if (error?.stderr) console.error(String(error.stderr).trim());
  // An installed but stale provider client can list voices successfully while
  // synthesis is rejected. Upgrade before substituting the channel narrator.
  console.error('Install/update it with: python -m pip install --upgrade edge-tts');
  process.exit(1);
}
let cursor = 0;
const timedPhrases = phrases.map((phrase, index) => {
  const startSeconds = cursor;
  const endSeconds = startSeconds + audioDurations[index];
  cursor = endSeconds;
  return {
    id: phrase.id,
    text: phrase.text,
    startSeconds,
    endSeconds,
    audioDurationSeconds: audioDurations[index],
    wordCount: phrase.wordCount,
  };
});

const ffmpegList = path.join(tempDir, 'concat.txt');
fs.writeFileSync(ffmpegList, generated.map((file) => `file '${file.replace(/'/g, "'\\''")}'`).join('\n') + '\n');
try {
  execFileSync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', ffmpegList, '-c', 'copy', out], {stdio: ['ignore', 'ignore', 'pipe']});
} catch (error) {
  console.error('\nUnable to combine phrase audio. ffmpeg is required.');
  if (error?.stderr) console.error(String(error.stderr).trim());
  process.exit(1);
}

fs.writeFileSync(generatedNarration, `// GENERATED FILE. DO NOT EDIT.\nexport const narrationCues = ${JSON.stringify(timedPhrases, null, 2)} as const;\n`);
fs.writeFileSync(cacheFile, JSON.stringify({
  version: CACHE_VERSION,
  key: cacheKey,
  source: narrationFile,
  voice,
  maxWords,
  rate: globalRate,
  targetWpm: targetWpm || DEFAULT_WPM,
  appliedRate,
  audioDurationSeconds: cursor,
  timedPhrases,
}, null, 2) + '\n');
fs.rmSync(tempDir, {recursive: true, force: true});
