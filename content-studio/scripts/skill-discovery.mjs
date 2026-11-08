// Discover the canonical skill tree once for installation and documentation checks.
import fs from 'node:fs';
import path from 'node:path';

const ignored = new Set(['node_modules', 'dist', '.local', 'tmp']);
const validName = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function discoverSkills(root) {
  const found = [];
  const names = new Map();
  function walk(folder) {
    for (const entry of fs.readdirSync(folder, {withFileTypes: true})) {
      const file = path.join(folder, entry.name);
      if (entry.isDirectory()) {
        if (!ignored.has(entry.name)) walk(file);
      } else if (entry.isFile() && entry.name === 'SKILL.md') {
        const text = fs.readFileSync(file, 'utf8');
        const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)?.[1];
        if (!frontmatter) throw new Error(`Missing skill frontmatter: ${file}`);
        const name = frontmatter.match(/^name:\s*['"]?([^'"\r\n]+)['"]?\s*$/m)?.[1];
        const description = frontmatter.match(/^description:\s*(.+)$/m)?.[1];
        if (!name || !validName.test(name) || !description)
          throw new Error(`Invalid skill name or description: ${file}`);
        if (names.has(name)) throw new Error(`Duplicate skill name ${name}: ${names.get(name)} and ${file}`);
        const registry = path.join(folder, 'methods.json');
        if (fs.existsSync(registry)) {
          const methods = JSON.parse(fs.readFileSync(registry, 'utf8')).methods;
          if (!Array.isArray(methods)) throw new Error(`Invalid method registry: ${registry}`);
          const ids = new Set();
          for (const method of methods) {
            if (!validName.test(method.id ?? '') || ids.has(method.id))
              throw new Error(`Invalid or duplicate method ID: ${registry}`);
            ids.add(method.id);
            if (!['supported', 'unsupported'].includes(method.status))
              throw new Error(`Invalid method status: ${registry}`);
            if (method.status === 'supported') {
              const script = path.resolve(folder, method.script ?? '');
              if (!script.startsWith(folder + path.sep) || !fs.statSync(script, {throwIfNoEntry: false})?.isFile())
                throw new Error(`Missing method script: ${registry} ${method.id}`);
            } else if (method.script) {
              throw new Error(`Unsupported method must not claim a script: ${registry} ${method.id}`);
            }
          }
        }
        names.set(name, file);
        found.push({name, folder, entry: file});
      }
    }
  }
  walk(root);
  return found.sort((a, b) => a.name.localeCompare(b.name));
}
