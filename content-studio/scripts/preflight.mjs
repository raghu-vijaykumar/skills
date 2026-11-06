// Production and package gates consume the exact human-reviewed plan revision.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function validatePreflight(draft, phase = 'start') {
  const base = path.join(draft, '.content-studio', 'preflight');
  const read = (name) => {
    try { return JSON.parse(fs.readFileSync(path.join(base, name), 'utf8')); }
    catch { throw new Error(`Preflight ${name} is missing or invalid; review and approve the production plan first`); }
  };
  const plan = read('plan.json');
  const approval = read('approval.json');
  const checklist = read('checklist.json');
  if (!Array.isArray(plan.steps) || !plan.steps.length) throw new Error('Preflight plan has no steps');
  // Match Python's byte-for-byte plan fingerprint, including reviewer-visible formatting.
  const digest = crypto.createHash('sha256').update(fs.readFileSync(path.join(base, 'plan.json'))).digest('hex');
  if (!approval.review_note || approval.plan_sha256 !== digest || checklist.plan_sha256 !== digest)
    throw new Error('Preflight approval is missing or stale; review the current plan again');
  if (!Array.isArray(checklist.items) || checklist.items.length !== plan.steps.length ||
      checklist.items.some((item, index) => item.id !== plan.steps[index].id))
    throw new Error('Preflight checklist does not match the approved steps');
  if (phase === 'complete') {
    const pending = checklist.items.filter((item, index) =>
      !(item.status === 'done' && Array.isArray(item.evidence) && item.evidence.length) &&
      !(item.status === 'not_applicable' && !plan.steps[index].required && item.reason));
    if (pending.length) throw new Error(`Preflight checklist incomplete: ${pending.map((item) => item.id).join(', ')}`);
  } else if (phase !== 'start') throw new Error(`Unknown preflight phase: ${phase}`);
  return {plan, approval, checklist};
}
