import { randomUUID } from "node:crypto";
import { WebSocketServer } from "ws";

// Relays jobs to the Chrome extension over a localhost WebSocket.
// The extension connects out to us (extensions cannot accept inbound connections),
// authenticates with a shared token, then receives jobs and reports results.
export class Bridge {
  constructor({ port, token, log = console.error }) {
    this.port = port;
    this.token = token;
    this.log = log;
    this.socket = null; // the single authenticated extension connection
    this.jobs = new Map(); // id -> { job, status, result, resolve }
  }

  start() {
    return new Promise((resolve, reject) => {
      this.wss = new WebSocketServer({ host: "127.0.0.1", port: this.port });
      this.wss.once("listening", () => {
        this.port = this.wss.address().port;
        resolve();
      });
      this.wss.once("error", reject);
      this.wss.on("connection", (ws, req) => this.#onConnection(ws, req));
    });
  }

  close() {
    for (const client of this.wss?.clients ?? []) client.terminate();
    return new Promise((resolve) => (this.wss ? this.wss.close(() => resolve()) : resolve()));
  }

  get connected() {
    return this.socket !== null;
  }

  #onConnection(ws, req) {
    // Browsers always send Origin; only our extension should be talking to us.
    const origin = req.headers.origin ?? "";
    if (origin && !origin.startsWith("chrome-extension://")) {
      ws.close(1008, "forbidden origin");
      return;
    }

    let authed = false;
    const authTimer = setTimeout(() => ws.close(1008, "auth timeout"), 5000);

    ws.on("message", (raw) => {
      let msg;
      try {
        msg = JSON.parse(raw.toString());
      } catch {
        return;
      }

      if (!authed) {
        if (msg.type !== "hello" || msg.token !== this.token) {
          ws.close(1008, "bad token");
          return;
        }
        authed = true;
        clearTimeout(authTimer);
        this.socket?.close(1000, "replaced by newer connection");
        this.socket = ws;
        ws.send(JSON.stringify({ type: "welcome" }));
        this.log(`[postmaster] extension connected (${msg.version ?? "unknown version"})`);
        this.#flushQueued();
        return;
      }

      if (msg.type === "result") this.#onResult(msg);
      // "ping" messages only exist to keep the extension's service worker alive.
    });

    ws.on("close", () => {
      clearTimeout(authTimer);
      if (this.socket === ws) {
        this.socket = null;
        this.log("[postmaster] extension disconnected");
      }
    });
  }

  #send(entry) {
    entry.status = "dispatched";
    this.socket.send(JSON.stringify({ type: "job", job: entry.job }));
  }

  #flushQueued() {
    for (const entry of this.jobs.values()) {
      if (entry.status === "queued") this.#send(entry);
    }
  }

  #onResult({ id, ok, url, message, mode }) {
    const entry = this.jobs.get(id);
    if (!entry || entry.result) return;
    entry.status = ok ? "succeeded" : "failed";
    entry.result = { ok: Boolean(ok), url: url ?? null, message: message ?? null, mode: mode ?? null };
    entry.resolve();
  }

  // Queues a job and waits up to `waitMs` for the extension to finish it.
  // Returns the job record either way; callers can poll with getJob() after a timeout.
  async submit(payload, { waitMs = 90_000 } = {}) {
    const id = randomUUID();
    let resolve;
    const done = new Promise((r) => (resolve = r));
    const entry = { job: { id, ...payload }, status: "queued", result: null, resolve, createdAt: Date.now() };
    this.jobs.set(id, entry);
    if (this.socket) this.#send(entry);

    let timer;
    await Promise.race([done, new Promise((r) => (timer = setTimeout(r, waitMs)))]);
    clearTimeout(timer);
    return this.getJob(id);
  }

  getJob(id) {
    const entry = this.jobs.get(id);
    if (!entry) return null;
    return { id, platform: entry.job.platform, status: entry.status, result: entry.result };
  }
}
