import { ENDPOINTS } from './config';
import { getToken } from './auth';

/**
 * Chat stream isteği gönderir, olayları callback'lerle bildirir.
 *
 * @param {string} message
 * @param {Array}  conversationHistory
 * @param {{ onNode, onToken, onDone, onError }} callbacks
 */
export async function sendChatStream(message, conversationHistory, callbacks) {
  const { onNode, onToken, onDone, onError } = callbacks;

  const response = await fetch(ENDPOINTS.chatStream, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let fullResponse = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;

      let event;
      try {
        event = JSON.parse(line.slice(6));
      } catch {
        continue;
      }

      if (event.type === 'node') onNode?.(event.node);

      if (event.type === 'token') {
        fullResponse += event.content;
        onToken?.(fullResponse);
      }

      if (event.type === 'done') {
        const final = event.full_response || fullResponse;
        onDone?.(final);
      }

      if (event.type === 'error') {
        throw new Error(event.message);
      }
    }
  }
}
