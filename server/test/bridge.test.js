import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import WebSocket from "ws";
import { Bridge } from "../src/bridge.js";
import { createServer } from "../src/tools.js";

const TOKEN = "test-token";
let bridge, client;

// Stands in for the Chrome extension: authenticates, then answers every job with `reply`.
function fakeExtension({ token = TOKEN, origin = "chrome-extension://abc", reply } = {}) {
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.port}`, { origin });
  const closed = new Promise((resolve) => ws.on("close", (code, reason) => resolve(reason.toString())));
  const ready = new Promise((resolve) => {
    ws.on("open", () => ws.send(JSON.stringify({ type: "hello", token })));
    ws.on("message", (raw) => {
      const msg = JSON.parse(raw);
      if (msg.type === "welcome") resolve();
      if (msg.type === "job") ws.send(JSON.stringify({ type: "result", id: msg.job.id, ...reply(msg.job) }));
    });
  });
  return { ws, ready, closed };
}

const call = async (name, args = {}) => {
  const res = await client.callTool({ name, arguments: args });
  return { ...res, body: JSON.parse(res.content[0].text) };
};

before(async () => {
  bridge = new Bridge({ port: 0, token: TOKEN, log: () => {} });
  await bridge.start();
  const [a, b] = InMemoryTransport.createLinkedPair();
  await createServer(bridge).connect(a);
  client = new Client({ name: "test", version: "0" });
  await client.connect(b);
});

after(async () => {
  await client.close();
  await bridge.close();
});

test("rejects a wrong token", async () => {
  const ext = fakeExtension({ token: "nope", reply: () => ({}) });
  assert.equal(await ext.closed, "bad token");
  assert.equal(bridge.connected, false);
});

test("rejects non-extension origins", async () => {
  const ext = fakeExtension({ origin: "https://evil.example", reply: () => ({}) });
  assert.equal(await ext.closed, "forbidden origin");
});

test("rejects text over the platform limit", async () => {
  const res = await call("create_post", { platform: "x", text: "a".repeat(281) });
  assert.equal(res.isError, true);
});

test("relays a post to the extension and returns its result", async () => {
  const seen = [];
  const ext = fakeExtension({ reply: (job) => (seen.push(job), { ok: true, mode: "review", message: "filled" }) });
  await ext.ready;
  assert.equal((await call("extension_status")).body.connected, true);

  const res = await call("create_post", { platform: "linkedin", text: "hello" });
  assert.equal(res.body.status, "succeeded");
  assert.deepEqual(res.body.result, { ok: true, url: null, message: "filled", mode: "review" });
  assert.equal(seen[0].text, "hello");
  assert.equal((await call("get_job", { id: res.body.id })).body.status, "succeeded");
  ext.ws.close();
  await ext.closed;
});

test("queues jobs until the extension connects", async () => {
  const pending = bridge.submit({ kind: "post", platform: "x", text: "later" }, { waitMs: 5000 });
  const ext = fakeExtension({ reply: () => ({ ok: false, message: "not logged in" }) });
  const job = await pending;
  assert.equal(job.status, "failed");
  assert.equal(job.result.message, "not logged in");
  ext.ws.close();
  await ext.closed;
});
