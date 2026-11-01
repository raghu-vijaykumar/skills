// Prefer a clean Git revision; approved edit-only workspaces retain a hash receipt.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';

export function sourceRevision(cwd, draft) {
  try {
    const root = execFileSync('git', ['-C', cwd, 'rev-parse', '--show-toplevel'],
      {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']}).trim();
    if (path.resolve(root).toLowerCase() !== path.resolve(cwd).toLowerCase())
      throw new Error('Git root differs from channel root');
    const rel = path.relative(cwd, draft);
    const changed = execFileSync('git', ['-C', cwd, 'status', '--porcelain', '--', rel], {encoding: 'utf8'}).trim();
    if (changed) throw new Error('Commit draft source and approved package before publishing');
    return execFileSync('git', ['-C', cwd, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim();
  } catch (error) {
    if (error.message?.includes('Commit draft') || error.message?.includes('Git root differs')) throw error;
    const approval = path.join(draft, 'package-approval.json');
    if (!fs.existsSync(approval)) throw new Error('No Git repository or approved source package');
    return `approved:${createHash('sha256').update(fs.readFileSync(approval)).digest('hex')}`;
  }
}
