import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

export const PLATFORMS = {
  x: { name: "X (Twitter)", maxLength: 280 },
  linkedin: { name: "LinkedIn", maxLength: 3000 },
};

const text = (value) => ({ content: [{ type: "text", text: JSON.stringify(value, null, 2) }] });

export function createServer(bridge) {
  const server = new McpServer({ name: "postmaster", version: "0.1.0" });

  server.registerTool(
    "list_platforms",
    { description: "List the social platforms Postmaster can post to." },
    async () => text(Object.entries(PLATFORMS).map(([id, p]) => ({ id, ...p })))
  );

  server.registerTool(
    "extension_status",
    { description: "Check whether the Postmaster Chrome extension is connected." },
    async () => text({ connected: bridge.connected, port: bridge.port })
  );

  server.registerTool(
    "create_post",
    {
      description:
        "Post text to a social platform from the user's logged-in Chrome. Depending on the extension's " +
        "settings the post is either submitted automatically or left in the composer for the user to review " +
        "and click Post themselves (the result's `mode` says which).",
      inputSchema: {
        platform: z.enum(Object.keys(PLATFORMS)),
        text: z.string().min(1),
      },
    },
    async ({ platform, text: body }) => {
      const { maxLength } = PLATFORMS[platform];
      if (body.length > maxLength) {
        return { ...text({ error: `Text is ${body.length} characters; ${platform} allows ${maxLength}.` }), isError: true };
      }
      const job = await bridge.submit({ kind: "post", platform, text: body });
      if (job.status === "queued") {
        job.note = "Extension is not connected; the job will run once it connects. Poll with get_job.";
      }
      return { ...text(job), isError: job.status === "failed" };
    }
  );

  server.registerTool(
    "get_job",
    {
      description: "Get the current status of a job returned by create_post.",
      inputSchema: { id: z.string() },
    },
    async ({ id }) => {
      const job = bridge.getJob(id);
      return job ? text(job) : { ...text({ error: `No job ${id}` }), isError: true };
    }
  );

  return server;
}
