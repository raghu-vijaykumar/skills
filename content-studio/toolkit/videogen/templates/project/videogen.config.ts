import {defineProject} from '@raghu-vijaykumar/videogen';
import {neutralTheme} from '@raghu-vijaykumar/videogen/runtime/themes';
import {coreExplainer} from '@raghu-vijaykumar/videogen/runtime/styles';

export default defineProject({
  entryPoint: 'src/entry.tsx',
  videosDir: 'videos',
  contentDir: 'content',
  theme: neutralTheme,
  styles: [coreExplainer],
  renderShortSide: 1080,
});
