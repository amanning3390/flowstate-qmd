import { watch, readFileSync, statSync, existsSync, writeFileSync } from "fs";
import { join } from "path";
import { homedir } from "os";
import { createStore, type SearchResult } from "../store.js";
import { withLLMSession } from "../llm.js";

const CACHE_DIR = join(homedir(), ".cache", "qmd");
const INTUITION_CACHE = join(CACHE_DIR, "intuition.json");

export type Intuition = {
  timestamp: number;
  query: string;
  memories: SearchResult[];
};

/**
 * Update the intuition cache with fresh memories based on current context
 */
export async function updateIntuition(context: string): Promise<void> {
  const store = createStore();
  
  try {
    // Only fetch top 3 most relevant memories to keep the "intuition" high-signal
    const results = await withLLMSession(async (session) => {
      // Hybrid query for context - uses both vector and FTS for best recall
      const searchResults = await store.hybridQuery(context, {
        limit: 3,
        minScore: 0.4
      });
      return searchResults;
    });

    const intuition: Intuition = {
      timestamp: Date.now(),
      query: context.slice(-200), // Store snippet for reference
      memories: results
    };

    if (!existsSync(CACHE_DIR)) {
      // mkdirSync is usually handled by store/llm init
    }
    
    writeFileSync(INTUITION_CACHE, JSON.stringify(intuition, null, 2));
    console.log(`[FLOW] Intuition updated (${results.length} memories)`);
  } catch (error) {
    console.error("[FLOW] Failed to update intuition:", error);
  } finally {
    store.close();
  }
}

/**
 * Main loop for the Flow Engine - Refined Event-Driven Watcher
 * 
 * Uses fs.watch for near-zero latency updates as the agent logs.
 * Includes a debouncer to prevent thrashing during rapid output.
 */
export async function startFlowEngine(targetFile: string): Promise<void> {
  if (!existsSync(targetFile)) {
    console.error(`[FLOW] Target file not found: ${targetFile}`);
    return;
  }

  console.log(`[FLOW] Monitoring ${targetFile} (Event-Driven)...`);
  
  let lastSize = statSync(targetFile).size;
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  const watcher = watch(targetFile, (eventType) => {
    if (eventType === 'change') {
      if (debounceTimer) clearTimeout(debounceTimer);
      
      debounceTimer = setTimeout(async () => {
        const stats = statSync(targetFile);
        if (stats.size > lastSize) {
          // File grew - new activity from agent or user
          const buffer = readFileSync(targetFile);
          // Read only the new part or the last 2000 chars
          const content = buffer.toString('utf-8', Math.max(0, stats.size - 2048));
          
          if (content.length > 50) {
            await updateIntuition(content);
            lastSize = stats.size;
          }
        }
      }, 1500); // 1.5s debounce: enough to let a thought finish, fast enough to be "intuitive"
    }
  });

  process.on('SIGINT', () => {
    watcher.close();
    process.exit(0);
  });
}
