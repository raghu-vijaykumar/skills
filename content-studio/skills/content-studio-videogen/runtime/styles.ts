import {defineContentStyle} from './project.ts';

// Styles describe editorial format rules; a theme supplies the visual identity.
export const coreExplainer = defineContentStyle({id: 'core-explainer', name: 'Core Explainer', formats: ['video', 'carousel', 'post']});
export const techDispatch = defineContentStyle({id: 'tech-dispatch', name: 'Tech Dispatch', formats: ['carousel', 'post']});
export const evidenceLab = defineContentStyle({id: 'evidence-lab', name: 'Evidence Lab', formats: ['video', 'carousel', 'post'], requiresFirsthandEvidence: true});
export const rapidTake = defineContentStyle({id: 'rapid-take', name: 'Rapid Take', formats: ['video']});
export const hairline = defineContentStyle({id: 'hairline', name: 'Hairline Animation', formats: ['video']});
export const builtInStyles = [coreExplainer, techDispatch, evidenceLab, rapidTake, hairline] as const;
