const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function streamAgentExecution({ payload, signal, onEvent }) {
  const response = await fetch(`${API_BASE}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Server responded with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split('\n\n');
    buffer = chunks.pop() || '';

    for (const chunk of chunks) {
      if (!chunk.startsWith('data: ')) continue;
      const rawJson = chunk.replace('data: ', '').trim();
      if (rawJson) {
        onEvent(JSON.parse(rawJson));
      }
    }
  }
}
