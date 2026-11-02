export type ContentFormat = 'video' | 'carousel' | 'post';
export type ContentStyle = Readonly<{
  id: string;
  name: string;
  look: string;
  use: string;
  formats: readonly ContentFormat[];
  tokens: string;
}>;
export const CONTENT_STYLES: readonly ContentStyle[];
export function contentStyle(id: string): ContentStyle | undefined;
