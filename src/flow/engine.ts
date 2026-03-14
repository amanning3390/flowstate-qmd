import {
  watchFile,
  unwatchFile,
  statSync,
  existsSync,
  writeFileSync,
  renameSync,
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
const WATCH_INTERVAL_MS = 1000; // Poll interval for fs.watchFile

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

// BUGFIX 1: Prevent Null-Byte Injection by capturing bytesRead
function readTail(path: string, fileSize: number, maxBytes: number = TAIL_BYTES): string {
  const bytesToRead = Math.min(fileSize, maxBytes);
  if (bytesToRead <= 0) return "";

  const buffer = Buffer.alloc(bytesToRead);
  const fd = openSync(path, "r");

  try {
    const position = Math.max(0, fileSize - bytesToRead);
    const bytesRead = readSync(fd, buffer, 0, bytesToRead, position);
    // Only parse the actual bytes read, ignoring trailing \0 allocations
    return buffer.subarray(0, bytesRead).toString("utf-8");
  } finally {
    closeSync(fd);
  }
}

// BUGFIX 2: Atomic Cache Writing
export async function updateIntuition(context: string, isLiteMode: boolean = false): Promise<void> {
  const store = createStore();
  try {
    const results = await hybridQuery(store, context, {
      limit: 3,
      minScore: 0.4,
      useLiteModels: isLiteMode // Pass lite mode flag down to the store
    });

    const intuition: Intuition = {
      timestamp: Date.now(),
      query: context.slice(-200),
      memories: results,
    };

    ensureCacheDir();
    
    // Write to a temporary file first, then atomically rename
    const tempCachePath = `${INTUITION_CACHE}.tmp`;
    writeFileSync(tempCachePath, JSON.stringify(intuition, null, 2));
    renameSync(tempCachePath, INTUITION_CACHE);
    
    console.log(`[FLOW] Intuition updated (${results.length} memories)`);
  } catch (error) {
    console.error("[FLOW] Failed to update intuition:", error);
  } finally {
    store.close();
  }
}

// BUGFIX 3: Resilient File Watching using fs.watchFile
export async function startFlowEngine(targetFile: string, isLiteMode: boolean = false): Promise<void> {
  if (!existsSync(targetFile)) {
    throw new Error(`[FLOW] Target file not found: ${targetFile}`);
  }

  ensureCacheDir();
  console.log(`[FLOW] Monitoring ${targetFile} (Polling Mode)...`);
  if (isLiteMode) console.log(`[FLOW] Running in LITE MODE (0.8B models)`);

  let lastSize = statSync(targetFile).size;
  let updateInFlight = false;

  // fs.watchFile survives file rotations natively by polling the stat object
  watchFile(targetFile, { interval: WATCH_INTERVAL_MS }, async (curr, prev) => {
    if (updateInFlight) return;
    
    try {
      updateInFlight = true;

      if (curr.size < lastSize) {
        console.log("[FLOW] Target file was truncated or rotated; resetting state.");
        lastSize = 0;
      }

      if (curr.size === lastSize) return;

      const content = readTail(targetFile, curr.size);
      lastSize = curr.size;

      if (content.trim().length < MIN_CONTEXT_CHARS) return;

      await updateIntuition(content, isLiteMode);
    } catch (err) {
      console.error("[FLOW] Watcher error:", err);
    } finally {
      updateInFlight = false;
    }
  });

  const shutdown = (signal: string, exitCode: number): void => {
    unwatchFile(targetFile);
    if (signal === "SIGINT") console.log("\n[FLOW] Stopped.");
    process.exit(exitCode);
  };

  process.on("SIGINT", () => shutdown("SIGINT", 0));
  process.on("SIGTERM", () => shutdown("SIGTERM", 0));
}