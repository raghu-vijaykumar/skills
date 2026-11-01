import {loadContentPackage} from './content-package.mjs';

try {
  const id = process.argv[2];
  const loaded = loadContentPackage(id);
  const count = loaded.config.editions.carousel?.slides.length ?? 0;
  console.log(`Content: ${id} valid (${loaded.style.name}, ${count} carousel slide(s), ${loaded.config.editions.post ? 'post' : 'no post'})`);
} catch (error) {
  console.error(`Content: ${error.message}`);
  process.exit(1);
}
