// Deterministic OpenAI-compatible provider for end-to-end tests.
//
// Point the back-end at it with LLM_BASE_URL=http://localhost:<port>/v1 and any
// LLM_API_KEY. It echoes the newest user turn so tests can assert that the
// message actually reached the provider, and streams it in pieces so the
// front-end exercises the streaming path rather than a single chunk.
import { createServer } from "node:http";

const port = Number(process.env.MOCK_LLM_PORT ?? 4010);

function chunkEvent(content) {
  return {
    id: "chatcmpl-e2e",
    object: "chat.completion.chunk",
    created: 0,
    model: "e2e/mock",
    choices: [{ index: 0, delta: { content }, finish_reason: null }],
  };
}

const finishEvent = {
  id: "chatcmpl-e2e",
  object: "chat.completion.chunk",
  created: 0,
  model: "e2e/mock",
  choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
};

const server = createServer((request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }

  if (request.method !== "POST" || !request.url?.endsWith("/chat/completions")) {
    response.writeHead(404);
    response.end();
    return;
  }

  let body = "";
  request.on("data", (chunk) => {
    body += chunk;
  });
  request.on("end", () => {
    let payload = {};
    try {
      payload = JSON.parse(body || "{}");
    } catch {
      payload = {};
    }

    const messages = Array.isArray(payload.messages) ? payload.messages : [];
    const lastUser = [...messages].reverse().find((message) => message.role === "user");
    const reply = `Mock reply: ${lastUser?.content ?? "nothing"}`;

    response.writeHead(200, {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      connection: "keep-alive",
    });
    response.flushHeaders();

    const pieces = reply.match(/.{1,8}/gs) ?? [reply];
    let index = 0;
    const timer = setInterval(() => {
      if (index < pieces.length) {
        response.write(`data: ${JSON.stringify(chunkEvent(pieces[index]))}\n\n`);
        index += 1;
        return;
      }

      clearInterval(timer);
      response.write(`data: ${JSON.stringify(finishEvent)}\n\n`);
      response.write("data: [DONE]\n\n");
      response.end();
    }, 15);
  });
});

server.listen(port, () => {
  console.log(`mock llm listening on http://localhost:${port}`);
});
