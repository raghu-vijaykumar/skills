import type {EasingName} from './types.ts';

export function ease(value: number, name: EasingName = 'easeInOut'): number {
  const normalize = (result: number) => {
    if (Math.abs(result) < 1e-12) return 0;
    if (Math.abs(result - 1) < 1e-12) return 1;
    return result;
  };

  const t = Math.max(0, Math.min(1, value));
  switch (name) {
    case 'linear':
      return normalize(t);
    case 'easeIn':
      return normalize(t * t);
    case 'easeOut':
      return normalize(1 - (1 - t) * (1 - t));
    case 'backOut': {
      const c1 = 1.70158;
      const c3 = c1 + 1;
      const out = 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
      return normalize(out);
    }
    case 'easeInOut':
    default:
      return normalize(t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  }
}
