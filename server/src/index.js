#!/usr/bin/env node
import { randomBytes } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Bridge } from "./bridge.js";
import { createServer } from "./tools.js";

// stdout carries the MCP protocol, so all logging goes to stderr.
const log = (...args) => console.error(...args);

function loadToken() {
  if (process.env.POSTMASTER_TOKEN) return process.env.POSTMASTER_TOKEN;
  const dir = join(homedir(), ".postmaster");
  const file = join(dir, "token");
  try {
    return readFileSync(file, "utf8").trim();
  } catch {
    mkdirSync(dir, { recursive: true, mode: 0o700 });
    const token = randomBytes(24).toString("base64url");
    writeFileSync(file, token + "\n", { mode: 0o600 });
    log(`[postmaster] generated pairing token in ${file}`);
    return token;
  }
}

async function main() {
  const port = Number(process.env.POSTMASTER_PORT ?? 17893);
  const bridge = new Bridge({ port, token: loadToken(), log });
  try {
    await bridge.start();
  } catch (err) {
    if (err.code === "EADDRINUSE") {
      log(`[postmaster] port ${port} is in use; another postmaster server is probably running. Set POSTMASTER_PORT to change it.`);
      process.exit(1);
    }
    throw err;
  }
  log(`[postmaster] waiting for extension on ws://127.0.0.1:${bridge.port}`);

  const server = createServer(bridge);
  await server.connect(new StdioServerTransport());

  // The WebSocket server would otherwise keep us alive after the MCP client goes away.
  process.stdin.on("close", async () => {
    await bridge.close();
    process.exit(0);
  });
}

main().catch((err) => {
  log(err);
  process.exit(1);
});
