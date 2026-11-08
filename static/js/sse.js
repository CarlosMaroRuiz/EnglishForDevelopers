/*
 * Minimal Server-Sent Events (SSE) client for the English Tutor app.
 *
 * Posts a JSON body to `url` and reads the `text/event-stream` response,
 * dispatching each parsed event to the matching handler.
 *
 * Usage:
 *   await streamSSE('/api/chat/stream', { message, scenario }, {
 *       delta: (event) => { ... },   // event.text
 *       done:  (event) => { ... },   // event.analysis / event.data
 *       error: (event) => { ... },   // event.message
 *   });
 */
async function streamSSE(url, body, handlers) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        let message = `HTTP error! status: ${response.status}`;
        try {
            const err = await response.json();
            if (err && err.error) message = err.error;
        } catch (_) { /* ignore non-JSON error bodies */ }
        const error = new Error(message);
        if (handlers.error) {
            handlers.error(error);
            return;
        }
        throw error;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const chunks = buffer.split('\n\n');
        buffer = chunks.pop();

        for (const chunk of chunks) {
            let data = '';
            for (const line of chunk.split('\n')) {
                if (line.startsWith('data:')) {
                    data += line.slice(5).trim();
                }
            }
            if (!data) continue;

            try {
                const event = JSON.parse(data);
                const handler = handlers[event.type];
                if (handler) handler(event);
            } catch (err) {
                console.error('SSE parse error:', err, data);
            }
        }
    }
}
