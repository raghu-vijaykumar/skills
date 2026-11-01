export async function sendMessage({token, chatId, text, disableWebPagePreview = true}) {
  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: 'HTML',
      disable_web_page_preview: disableWebPagePreview,
    }),
  });
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Telegram returned a non-JSON response (HTTP ${response.status}).`);
  }
  if (!body.ok) {
    throw new Error(`Telegram API error: ${body.description ?? response.status}`);
  }
  return body.result;
}

export async function sendMessageParts({token, chatId, chunks, disableWebPagePreview = true}) {
  const results = [];
  for (const chunk of chunks) {
    results.push(await sendMessage({token, chatId, text: chunk, disableWebPagePreview}));
  }
  return results;
}
