// Terminal styling and a prettifier that turns the Telegram HTML message into
// readable, coloured console output (used by --dry-run and the status lines).

const useColor =
  !('NO_COLOR' in process.env) &&
  (process.env.FORCE_COLOR
    ? process.env.FORCE_COLOR !== '0'
    : Boolean(process.stdout.isTTY));

const wrap = (code) => (text) => (useColor ? `\u001b[${code}m${text}\u001b[0m` : String(text));

export const bold = wrap('1');
export const dim = wrap('2');
export const cyan = wrap('36');
export const green = wrap('32');
export const red = wrap('31');
export const yellow = wrap('33');

export const ok = green('✓');
export const fail = red('✗');

function decodeEntities(text) {
  return String(text)
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

export function renderPretty(html) {
  let text = String(html);
  text = text.replace(/<a href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/g, (_, url, label) => {
    const clean = decodeEntities(label.replace(/<[^>]+>/g, '')).trim();
    return `${cyan(clean)} ${dim(`(${url})`)}`;
  });
  text = text.replace(/<(b|strong)>([\s\S]*?)<\/\1>/g, (_, _tag, inner) => bold(inner));
  text = text.replace(/<i>([\s\S]*?)<\/i>/g, (_, inner) => dim(inner));
  text = decodeEntities(text);
  text = text.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n');
  return text.replace(/^\n+|\n+$/g, '');
}
