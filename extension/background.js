import { PLATFORMS, fillComposer } from "./platforms.js";

const DEFAULTS = { port: 17893, token: "", autoSubmit: false };
const RECONNECT_MS = 3_000;
const KEEPALIVE_MS = 20_000; // WebSocket traffic keeps an MV3 service worker alive (Chrome 116+)

let ws = null;
let keepalive = null;
let reconnectTimer = null;

const getSettings = async () => ({ ...DEFAULTS, ...(await chrome.storage.local.get(Object.keys(DEFAULTS))) });
const setStatus = (status) => chrome.storage.local.set({ status });

async function connect() {
  if (ws && ws.readyState <= WebSocket.OPEN) return;
  clearTimeout(reconnectTimer);

  const { port, token } = await getSettings();
  if (!token) {
    await setStatus("Not paired: paste the token from ~/.postmaster/token");
    return;
  }

  const socket = new WebSocket(`ws://127.0.0.1:${port}`);
  ws = socket;

  socket.onopen = () => {
    socket.send(JSON.stringify({ type: "hello", token, version: chrome.runtime.getManifest().version }));
    keepalive = setInterval(() => socket.send(JSON.stringify({ type: "ping" })), KEEPALIVE_MS);
  };

  socket.onmessage = async (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "welcome") await setStatus("Connected");
    if (msg.type === "job") {
      const result = await runJob(msg.job);
      if (socket.readyState === WebSocket.OPEN)
        socket.send(JSON.stringify({ type: "result", id: msg.job.id, ...result }));
    }
  };

  socket.onclose = async (event) => {
    clearInterval(keepalive);
    if (ws !== socket) return; // replaced by a newer connection
    ws = null;
    await setStatus(event.reason === "bad token" ? "Token rejected by server" : "Server not running");
    reconnectTimer = setTimeout(connect, RECONNECT_MS);
  };
}

function waitForTabLoad(tabId) {
  return new Promise((resolve) => {
    const listener = (id, info) => {
      if (id === tabId && info.status === "complete") {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function runJob(job) {
  const platform = PLATFORMS[job.platform];
  if (!platform) return { ok: false, message: `Unsupported platform: ${job.platform}` };

  const { autoSubmit } = await getSettings();
  try {
    const tab = await chrome.tabs.create({ url: platform.url, active: true });
    await waitForTabLoad(tab.id);
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: fillComposer,
      args: [{ editor: platform.editor, submit: platform.submit, text: job.text, autoSubmit }],
    });
    return result ?? { ok: false, message: "Composer script did not return a result" };
  } catch (err) {
    return { ok: false, message: err.message ?? String(err) };
  }
}

// Reconnect when settings change, and periodically in case the worker was suspended.
chrome.storage.onChanged.addListener((changes) => {
  if (changes.token || changes.port) {
    ws?.close();
    connect();
  }
});
chrome.alarms.create("reconnect", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(connect);
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();
