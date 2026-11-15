// Leaf-skill entrypoint for the maintained videogen narration aligner.
import {alignNarration} from '../../scripts/align-narration.mjs';

const folder = process.argv[2];
if (!folder) throw new Error('Usage: node align-narration.mjs <draft-folder>');
const result = alignNarration(folder);
console.log(`Aligned ${result.scenes} cues to ${result.duration.toFixed(2)}s`);
