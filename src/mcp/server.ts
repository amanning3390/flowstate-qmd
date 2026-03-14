import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { hybridQuery, createStore } from "../store.js";
import { readFileSync, existsSync } from "fs";

const server = new McpServer({
  name: "FlowState-QMD",
  version: "1.0.0"
});

// Expose a direct MCP tool for Hermes to fetch its own intuition 
// instantly, bypassing the file watcher delay entirely.
server.tool(
  "fetch_anticipatory_context",
  "Fetch immediate, predictive context based on the current conversational state.",
  {
    recent_conversation: z.string().describe("The last 3-5 messages of the chat"),
    lite_mode: z.boolean().optional().describe("Use smaller, faster models for low VRAM")
  },
  async ({ recent_conversation, lite_mode }) => {
    const store = createStore();
    try {
      const results = await hybridQuery(store, recent_conversation, {
        limit: 3,
        minScore: 0.4,
        useLiteModels: lite_mode ?? false
      });
      
      return {
        content: [{ 
          type: "text", 
          text: JSON.stringify(results, null, 2) 
        }]
      };
    } finally {
      store.close();
    }
  }
);

// Standard search tool implementation
server.tool(
  "search_qmd",
  "Search local QMD databases contextually",
  {
    query: z.string().describe("Natural language query to search for"),
    collection: z.string().optional().describe("Specifically search a subset of data"),
    limit: z.number().optional().describe("Max results to return (default: 5)")
  },
  async ({ query, collection, limit = 5 }) => {
    const store = createStore();
    try {
      const results = await hybridQuery(store, query, {
        limit,
        collection,
        minScore: 0.2
      });
      
      return {
        content: [{ 
          type: "text", 
          text: JSON.stringify(results.map(r => ({
             path: r.displayPath,
             title: r.title,
             snippet: r.bestChunk,
             score: r.score.toFixed(3)
          })), null, 2) 
        }]
      };
    } finally {
      store.close();
    }
  }
);

// Standard retrieval tool
server.tool(
  "read_qmd_doc",
  "Read full content of a QMD document",
  {
    path: z.string().describe("Document path/ID from search results")
  },
  async ({ path }) => {
    const store = createStore();
    try {
      const doc = store.findDocument(path, { includeBody: true });
      if ('error' in doc) {
        return {
          content: [{ type: "text", text: `Document not found. Did you mean:\n${doc.similarFiles.join("\n")}` }],
          isError: true
        };
      }
      
      return {
        content: [{ type: "text", text: doc.body || "No content." }]
      };
    } finally {
      store.close();
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("FlowState QMD MCP Server running on stdio");
}

main().catch(console.error);