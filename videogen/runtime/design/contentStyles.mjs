// A content style defines the editorial grammar across formats. Each edition
// chooses a delivery format without creating another style identity.
export const CONTENT_STYLES = Object.freeze([
  Object.freeze({
    id: 'core-explainer',
    name: 'Core Explainer',
    look: 'Dark cinematic',
    use: 'Mechanism-led technical explanations',
    formats: Object.freeze(['video', 'carousel', 'post']),
    tokens: 'src/design/color.ts',
  }),
  Object.freeze({
    id: 'tech-dispatch',
    name: 'Tech Dispatch',
    look: 'Dark editorial',
    use: 'Source-led technology news and debate',
    formats: Object.freeze(['video', 'carousel', 'post']),
    tokens: 'src/design/techDispatch.ts',
  }),
  Object.freeze({
    id: 'evidence-lab',
    name: 'Evidence Lab',
    look: 'Dark investigative',
    use: 'Research-led investigations built around firsthand captures and reproducible findings',
    formats: Object.freeze(['video', 'carousel', 'post']),
    tokens: 'src/design/evidenceLab.ts',
  }),
]);

export const contentStyle = (id) => CONTENT_STYLES.find((style) => style.id === id);
