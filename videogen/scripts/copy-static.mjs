import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, 'runtime');
const target = path.join(root, 'dist');

// TypeScript emits code; keep CSS imported by the optional RippleGrid beside it.
function copyAssets(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const from = path.join(dir, entry.name);
    if (entry.isDirectory()) copyAssets(from);
    else if (entry.name.endsWith('.css')) {
      const to = path.join(target, path.relative(source, from));
      fs.mkdirSync(path.dirname(to), {recursive: true});
      fs.copyFileSync(from, to);
    }
  }
}
copyAssets(source);
