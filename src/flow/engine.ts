import {
  watch,
  statSync,
  existsSync,
  writeFileSync,
  readFileSync,
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

// 8KB tail captures ~2000 tokens of context, sufficient for most agent turns
// while staying fast enough for real-time updates
const TAIL_BYTES = 8192;
const MIN_CONTEXT_CHARS = 50;
const DEBOUNCE_MS = 1500;

export type Intuition = {
  timestamp: number;
  query: string;
  memories: HybridQueryResult[];
};

export type FlowTelemetry = {
  cacheHits: number;
  cacheMisses: number;
  lastHitAt: number | null;
  lastMissAt: number | null;
  totalRefreshes: number;
  avgRefreshMs: number;
};

const telemetry: FlowTelemetry = {
  cacheHits: 0,
  cacheMisses: 0,
  lastHitAt: null,
  lastMissAt: null,
  totalRefreshes: 0,
  avgRefreshMs: 0,
};

export function getFlowTelemetry(): FlowTelemetry {
  return { ...telemetry };
}

export function resetFlowTelemetry(): void {
  telemetry.cacheHits = 0;
  telemetry.cacheMisses = 0;
  telemetry.lastHitAt = null;
  telemetry.lastMissAt = null;
  telemetry.totalRefreshes = 0;
  telemetry.avgRefreshMs = 0;
}

function recordRefreshDuration(ms: number): void {
  const prev = telemetry.avgRefreshMs;
  const n = telemetry.totalRefreshes;
  telemetry.totalRefreshes = n + 1;
  telemetry.avgRefreshMs = n === 0 ? ms : (prev * n + ms) / (n + 1);
}

type FlowEngineRuntime = {
  watch: typeof watch;
  statSync: typeof statSync;
  existsSync: typeof existsSync;
  writeFileSync: typeof writeFileSync;
  readFileSync: typeof readFileSync;
  renameSync: typeof renameSync;
  mkdirSync: typeof mkdirSync;
  openSync: typeof openSync;
  closeSync: typeof closeSync;
  readSync: typeof readSync;
  homedir: typeof homedir;
  createStore: typeof createStore;
  hybridQuery: typeof hybridQuery;
};

const defaultRuntime: FlowEngineRuntime = {
  watch,
  statSync,
  existsSync,
  writeFileSync,
  readFileSync,
  renameSync,
  mkdirSync,
  openSync,
  closeSync,
  readSync,
  homedir,
  createStore,
  hybridQuery,
};

let runtimeOverrides: Partial<FlowEngineRuntime> = {};

function getRuntime(): FlowEngineRuntime {
  return {
    ...defaultRuntime,
    ...runtimeOverrides,
  };
}

function getCacheDir(): string {
  return join(getRuntime().homedir(), ".cache", "qmd");
}

function getIntuitionCachePath(): string {
  return join(getCacheDir(), "intuition.json");
}

export function setFlowEngineRuntimeForTests(overrides: Partial<FlowEngineRuntime> | null): void {
  runtimeOverrides = overrides ?? {};
}

function persistIntuitionCache(intuition: Intuition): void {
  const runtime = getRuntime();
  const intuitionCache = getIntuitionCachePath();
  const payload = JSON.stringify(intuition, null, 2);
  const tempCachePath = `${intuitionCache}.tmp`;

  if (typeof runtime.renameSync !== "function") {
    runtime.writeFileSync(intuitionCache, payload);
    return;
  }

  runtime.writeFileSync(tempCachePath, payload);
  try {
    runtime.renameSync(tempCachePath, intuitionCache);
  } catch {
    runtime.writeFileSync(intuitionCache, payload);
  }
}

export function readIntuitionCache(): Intuition | null {
  const runtime = getRuntime();
  const intuitionCache = getIntuitionCachePath();
  if (!runtime.existsSync(intuitionCache)) {
    telemetry.cacheMisses++;
    telemetry.lastMissAt = Date.now();
    return null;
  }

  try {
    const raw = runtime.readFileSync(intuitionCache, "utf-8");
    const result = JSON.parse(raw) as Intuition;
    telemetry.cacheHits++;
    telemetry.lastHitAt = Date.now();
    return result;
  } catch {
    telemetry.cacheMisses++;
    telemetry.lastMissAt = Date.now();
    return null;
  }
}

function ensureCacheDir(): void {
  const runtime = getRuntime();
  const cacheDir = getCacheDir();
  if (!runtime.existsSync(cacheDir)) {
    runtime.mkdirSync(cacheDir, { recursive: true });
  }
}

function getTelemetryPath(): string {
  return join(getCacheDir(), "telemetry.json");
}

function persistTelemetry(): void {
  const runtime = getRuntime();
  try {
    ensureCacheDir();
    runtime.writeFileSync(getTelemetryPath(), JSON.stringify(telemetry, null, 2));
  } catch {
    // Non-critical — telemetry loss is acceptable
  }
}

export function loadTelemetry(): FlowTelemetry {
  const runtime = getRuntime();
  const telemetryPath = getTelemetryPath();
  if (!runtime.existsSync(telemetryPath)) {
    return { ...telemetry };
  }
  try {
    const raw = runtime.readFileSync(telemetryPath, "utf-8");
    const loaded = JSON.parse(raw) as FlowTelemetry;
    Object.assign(telemetry, loaded);
    return { ...telemetry };
  } catch {
    return { ...telemetry };
  }
}

function readTail(path: string, fileSize: number, maxBytes: number = TAIL_BYTES): string {
  const runtime = getRuntime();
  const bytesToRead = Math.min(fileSize, maxBytes);
  if (bytesToRead <= 0) {
    return "";
  }

  const buffer = Buffer.alloc(bytesToRead);
  const fd = runtime.openSync(path, "r");

  try {
    runtime.readSync(fd, buffer, 0, bytesToRead, fileSize - bytesToRead);
    return buffer.toString("utf-8");
  } finally {
    runtime.closeSync(fd);
  }
}

/**
 * Update the intuition cache with fresh memories based on current context.
 * Uses the standalone hybridQuery() which manages its own LLM session.
 */
export async function updateIntuition(context: string, isLiteMode: boolean = false): Promise<void> {
  const runtime = getRuntime();
  const store = runtime.createStore();
  const startMs = Date.now();

  try {
    const results = await runtime.hybridQuery(store, context, {
      limit: 3,
      minScore: 0.4,
      liteMode: isLiteMode,
    });

    const intuition: Intuition = {
      timestamp: Date.now(),
      query: context.slice(-200),
      memories: results,
    };
    ensureCacheDir();
    persistIntuitionCache(intuition);
    recordRefreshDuration(Date.now() - startMs);
    persistTelemetry();

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
  const runtime = getRuntime();
  if (!runtime.existsSync(targetFile)) {
    throw new Error(`[FLOW] Target file not found: ${targetFile}`);
  }

  ensureCacheDir();

  console.log(`[FLOW] Monitoring ${targetFile} (Event-Driven)...`);
  console.log(`[FLOW] Intuition cache: ${getIntuitionCachePath()}`);
  console.log("[FLOW] Press Ctrl+C to stop.");

  let lastSize = runtime.statSync(targetFile).size;
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
      const stats = runtime.statSync(targetFile);

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

  const watcher = runtime.watch(targetFile, (eventType) => {
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
