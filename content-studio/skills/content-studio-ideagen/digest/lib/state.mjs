// Sent-item dedupe state is per channel, never part of the reusable skill.
import fs from 'node:fs';
import path from 'node:path';

const MAX_KEYS = 4000;
export function sentFile(workspace) { return path.join(workspace, 'analysis', 'digest', 'sent.json'); }
export function loadSentKeys(file) {
  if (!fs.existsSync(file)) return new Set();
  const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  return new Set((Array.isArray(parsed) ? parsed : parsed.keys ?? []).map(String));
}
export function saveSentKeys(keys, file) {
  const list = [...keys].sort();
  const trimmed = list.length > MAX_KEYS ? list.slice(-MAX_KEYS) : list;
  fs.mkdirSync(path.dirname(file), {recursive: true});
  fs.writeFileSync(file, JSON.stringify(trimmed, null, 2) + '\n');
  return trimmed.length;
}
