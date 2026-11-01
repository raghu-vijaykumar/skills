const USER_AGENT =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 content-studio-digest/1.0';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getText(url, {headers = {}, timeoutMs = 15000, retries = 2} = {}) {
  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        redirect: 'follow',
        signal: controller.signal,
        headers: {
          'User-Agent': USER_AGENT,
          Accept:
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.9',
          ...headers,
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} ${response.statusText}`);
      }
      return await response.text();
    } catch (error) {
      lastError = error;
      if (attempt < retries) await sleep(600 * (attempt + 1));
    } finally {
      clearTimeout(timer);
    }
  }
  throw lastError;
}

export async function getJson(url, opts = {}) {
  const text = await getText(url, {
    ...opts,
    headers: {
      Accept: 'application/json',
      ...(opts.headers ?? {}),
    },
  });
  return JSON.parse(text);
}
