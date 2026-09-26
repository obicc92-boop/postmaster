# Postmaster

A personal, local-only take on "let my AI agent post to social media from my browser".
Your agent calls an MCP server running on your machine; the server hands the job to a
Chrome extension, which types the post into the site's own composer using your
existing logged-in session. No cloud relay, no platform API keys, nothing leaves your machine.

```
AI agent ──MCP (stdio)──▶ server/ ──ws://127.0.0.1:17893──▶ extension/ ──▶ x.com / linkedin.com tab
```

Supported: **X** and **LinkedIn**, text posts.

## Setup

1. **Server**
   ```sh
   cd server && npm install
   claude mcp add postmaster -- node "$(pwd)/src/index.js"
   ```
   The first run creates a pairing token in `~/.postmaster/token`.
   (Other MCP clients: run `node /path/to/server/src/index.js` as a stdio server.)

2. **Extension**: open `chrome://extensions`, enable Developer mode, click
   **Load unpacked** and pick the `extension/` folder.

3. **Pair**: click the extension icon, paste the token from `~/.postmaster/token`, and
   save. The status should read **Connected** while your MCP client is running.

4. Make sure you're logged in to X and LinkedIn in that Chrome profile.

## Tools

| Tool | What it does |
| --- | --- |
| `list_platforms` | Supported platforms and their length limits |
| `extension_status` | Whether the extension is connected |
| `create_post` | `{ platform, text }`: opens the composer and fills it in |
| `get_job` | Status of an earlier `create_post` (e.g. one queued while the extension was offline) |

## Review mode vs. auto-submit

By default the extension only **fills in** the composer and leaves the tab open for you to
read it and click Post. Turn on "Submit posts automatically" in the popup to have it click
Post itself. Keep review mode until you trust your agent's output.

## Security

- The WebSocket listens on `127.0.0.1` only, rejects connections from web pages (non-extension
  `Origin`) and requires the pairing token. Without these, any website you visited could post as you.
- The extension only has host access to `x.com` and `www.linkedin.com`.
- Anything that can reach the MCP server can post as you, so only register it with agents you trust.

## When it breaks

Both sites change their markup without warning. Selectors live in one place,
`extension/platforms.js`. When a post times out "waiting for the composer" or "the Post button",
inspect the page and update them.

Automated posting may break a platform's terms of service. Keep the volume human-scale.

## Development

```sh
cd server && npm test   # drives the MCP tools end to end against a fake extension
```

To add a platform, add an entry to `extension/platforms.js` and `server/src/tools.js`, and add
the site to `host_permissions` in `extension/manifest.json`.
