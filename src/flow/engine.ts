import {
  watch,
  statSync,
  existsSync,
  writeFileSync,
  mkdirSync,
  openSync,
  closeSync,
  readSync,
} from "fs";
import { join } from "path";
import { homedir } from "os";
import { createStore, hybridQuery } from "../store.js";
import type { HybridQueryResult } from "../store.js";

const CACHE_DIR = join(homedir(), ".cache", "qmd");
const INTUITION_CACHE = join(CACHE_DIR, "intuition.json");
const TAIL_BYTES = 2048;
const MIN_CONTEXT_CHARS = 50;
const DEBOUNCE_MS = 1500;

export type Intuition = {
  timestamp: number;
  query: string;
  memories: HybridQueryResult[];
};

function ensureCacheDir(): void {
  if (!existsSync(CACHE_DIR)) {
    mkdirSync(CACHE_DIR, { recursive: true });
  }
}

function readTail(path: string, fileSize: number, maxBytes: number = TAIL_BYTES): string {
  const bytesToRead = Math.min(fileSize, maxBytes);
  if (bytesToRead <= 0) {
    return "";
  }

  const buffer = Buffer.alloc(bytesToRead);
  const fd = openSync(path, "r");

  try {
    readSync(fd, buffer, 0, bytesToRead, fileSize - bytesToRead);
    return buffer.toString("utf-8");
  } finally {
    closeSync(fd);
  }
}

/**
 * Update the intuition cache with fresh memories based on current context.
 * Uses the standalone hybridQuery() which manages its own LLM session.
 */
export async function updateIntuition(context: string, isLiteMode: boolean = false): Promise<void> {
  const store = createStore();

  try {
    const results = await hybridQuery(store, context, {
      limit: 3,
      minScore: 0.4,
      // @ts-ignore
      useLiteModels: isLiteMode
    });

    const intuition: Intuition = {
      timestamp: Date.now(),
      query: context.slice(-200),
      memories: results,
    };


    ensureCacheDir();
    const tempCachePath = `${INTUITION_CACHE}.tmp`;
    writeFileSync(tempCachePath, JSON.stringify(intuition, null, 2));
    // Atomic rename to prevent race conditions
    import("fs").then(fs => {
      fs.renameSync(tempCachePath, INTUITION_CACHE);
    }).catch(err => {
      // Fallback
      writeFileSync(INTUITION_CACHE, JSON.stringify(intuition, null, 2));
    });

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
export async function startFlowEngine(targetFile: string, isLiteMode: boolean = false): Promise<void> {
  if (!existsSync(targetFile)) {
    throw new Error(`[FLOW] Target file not found: ${targetFile}`);
  }

  ensureCacheDir();

  console.log(`[FLOW] Monitoring ${targetFile} (Event-Driven)...`);
  console.log(`[FLOW] Intuition cache: ${INTUITION_CACHE}`);
  console.log("[FLOW] Press Ctrl+C to stop.");

  let lastSize = statSync(targetFile).size;
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let updateInFlight = false;
  let rerunRequested = false;

  const processLatestChange = async (): Promise<void> => {
    if (updateInFlight) {
      rerunRequested = true;
      return;
    }

    updateInFlight = true;

    try {
      const stats = statSync(targetFile);

      if (stats.size < lastSize) {
        console.log("[FLOW] Target file was truncated or rotated; resetting watcher state.");
        lastSize = 0;
      }

      if (stats.size === lastSize) {
        return;
      }

      const content = readTail(targetFile, stats.size);
      lastSize = stats.size;

      if (content.trim().length < MIN_CONTEXT_CHARS) {
        return;
      }

      await updateIntuition(content, isLiteMode);
    } catch (err) {
      console.error("[FLOW] Watcher error:", err);
    } finally {
      updateInFlight = false;

      if (rerunRequested) {
        rerunRequested = false;
        void processLatestChange();
      }
    }
  };

  const watcher = watch(targetFile, (eventType) => {
    if (eventType !== "change") {
      return;
    }

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    debounceTimer = setTimeout(() => {
      void processLatestChange();
    }, DEBOUNCE_MS);
  });

  const shutdown = (signal: string, exitCode: number): void => {
    watcher.close();

    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }

    process.off("SIGINT", handleSigint);
    process.off("SIGTERM", handleSigterm);

    if (signal === "SIGINT") {
      console.log("\n[FLOW] Stopped.");
    }

    process.exit(exitCode);
  };

  const handleSigint = (): void => shutdown("SIGINT", 0);
  const handleSigterm = (): void => shutdown("SIGTERM", 0);

  process.on("SIGINT", handleSigint);
  process.on("SIGTERM", handleSigterm);
}
