import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {transform} from 'esbuild';

// Node 22 cannot strip TypeScript inside node_modules. Ship plain JavaScript
// validators while retaining their typed sources for toolkit development.
const toolkit = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceDir = path.join(toolkit, 'scripts', 'validation');
const outputDir = path.join(toolkit, 'dist', 'gates');
fs.mkdirSync(outputDir, {recursive: true});
for (const name of fs.readdirSync(sourceDir).filter((file) => file.endsWith('.mts'))) {
  const source = fs.readFileSync(path.join(sourceDir, name), 'utf8');
  const result = await transform(source, {loader: 'ts', format: 'esm', target: 'es2022', sourcefile: name});
  fs.writeFileSync(path.join(outputDir, name.replace(/\.mts$/, '.mjs')), result.code);
}
