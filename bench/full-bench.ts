/**
 * Full benchmark: FlowState cache read vs FTS search latency.
 * This measures the core value proposition: cache hits are orders of magnitude
 * faster than even the simplest search operation.
 * 
 * Skips LLM-dependent hybrid/vector search to avoid compilation requirements.
 */

import { createStore } from "../src/store.js";
import { readIntuitionCache } from "../src/flow/engine.js";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const BENCH_ROUNDS = 100;
const WARMUP_ROUNDS = 5;

type BenchResult = {
  name: string;
  description: string;
  rounds: number;
  minMs: number;
  maxMs: number;
  avgMs: number;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
};

function percentile(sorted: number[], p: number): number {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)]!;
}

function round(n: number, decimals = 3): number {
  return Math.round(n * 10 ** decimals) / 10 ** decimals;
}

function benchSync(name: string, description: string, fn: () => void): BenchResult {
  for (let i = 0; i < WARMUP_ROUNDS; i++) fn();
  const timings: number[] = [];
  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    fn();
    timings.push(performance.now() - start);
  }
  timings.sort((a, b) => a - b);
  return {
    name, description, rounds: BENCH_ROUNDS,
    minMs: round(timings[0]!), maxMs: round(timings[timings.length - 1]!),
    avgMs: round(timings.reduce((a, b) => a + b, 0) / timings.length),
    p50Ms: round(percentile(timings, 50)),
    p95Ms: round(percentile(timings, 95)),
    p99Ms: round(percentile(timings, 99)),
  };
}

async function benchAsync(name: string, description: string, fn: () => Promise<void>): Promise<BenchResult> {
  for (let i = 0; i < WARMUP_ROUNDS; i++) await fn();
  const timings: number[] = [];
  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    await fn();
    timings.push(performance.now() - start);
  }
  timings.sort((a, b) => a - b);
  return {
    name, description, rounds: BENCH_ROUNDS,
    minMs: round(timings[0]!), maxMs: round(timings[timings.length - 1]!),
    avgMs: round(timings.reduce((a, b) => a + b, 0) / timings.length),
    p50Ms: round(percentile(timings, 50)),
    p95Ms: round(percentile(timings, 95)),
    p99Ms: round(percentile(timings, 99)),
  };
}

async function main() {
  const dbPath = process.env.INDEX_PATH!;
  const store = createStore(dbPath);
  const results: BenchResult[] = [];

  // Ensure intuition cache exists with realistic content
  const cacheDir = join(homedir(), ".cache", "qmd");
  const cachePath = join(cacheDir, "intuition.json");
  const cacheExisted = existsSync(cachePath);
  if (!cacheExisted) {
    mkdirSync(cacheDir, { recursive: true });
    writeFileSync(cachePath, JSON.stringify({
      timestamp: Date.now(),
      query: "why did we revert the auth migration",
      memories: [
        { file: "CHANGELOG.md#auth-rollback", score: 0.92, title: "Auth rollback entry", snippet: "Reverted auth migration due to connection pool exhaustion under load. See ADR-017." },
        { file: "ADR-017.md", score: 0.88, title: "ADR-017: Phased Auth Rollout", snippet: "Decision: use phased rollout to avoid connection pool exhaustion." },
        { file: "docs/migration-runbook.md", score: 0.81, title: "Migration Runbook", snippet: "Steps to safely roll back auth changes in production." },
      ],
    }, null, 2));
  }

  // 1. FlowState anticipatory cache read (the fast path)
  results.push(benchSync(
    "FlowState cache read",
    "Read + parse intuition.json (the anticipatory cache hot path)",
    () => { readIntuitionCache(); }
  ));

  // 2. Raw JSON.parse of cache file
  results.push(benchSync(
    "Cache JSON.parse",
    "Raw readFileSync + JSON.parse of intuition.json",
    () => {
      const raw = readFileSync(cachePath, "utf-8");
      JSON.parse(raw);
    }
  ));

  // 3. FTS search (BM25) — the traditional RAG first step
  const ftsQueries = [
    "authentication middleware",
    "database migration rollback",
    "API rate limiting",
    "connection pool exhaustion",
    "error handling",
  ];
  for (const q of ftsQueries) {
    results.push(benchSync(
      `FTS search: "${q}"`,
      `BM25 full-text search over 31 indexed documents`,
      () => { store.searchFTS(q, 10); }
    ));
  }

  // 4. Store status call
  results.push(benchSync(
    "Store status",
    "MCP status tool equivalent",
    () => { store.getStatus(); }
  ));

  // 5. Document find by path
  results.push(benchSync(
    "Find document by path",
    "Single document retrieval by path",
    () => { store.findDocument("README.md", { includeBody: true }); }
  ));

  // 6. existsSync for cache miss
  results.push(benchSync(
    "Cache miss (existsSync)",
    "Check for non-existent cache file",
    () => { existsSync(join(cacheDir, "nonexistent-cache.json")); }
  ));

  store.close();

  // Cleanup synthetic cache
  if (!cacheExisted) {
    try { require("fs").unlinkSync(cachePath); } catch {}
  }

  // Summary
  const cacheAvg = results[0]!.avgMs;
  const ftsAvgs = results.filter(r => r.name.startsWith("FTS")).map(r => r.avgMs);
  const ftsAvg = ftsAvgs.reduce((a, b) => a + b, 0) / ftsAvgs.length;

  const output = {
    timestamp: new Date().toISOString(),
    environment: {
      node: process.version,
      platform: process.platform,
      arch: process.arch,
      indexedDocuments: 31,
      benchRounds: BENCH_ROUNDS,
      warmupRounds: WARMUP_ROUNDS,
    },
    results,
    summary: {
      cacheReadAvgMs: round(cacheAvg),
      ftsSearchAvgMs: round(ftsAvg),
      speedupFactor: round(ftsAvg / cacheAvg, 1),
      note: "FTS is the fastest traditional search. Hybrid/vector search with embedding + reranking adds 100-2000ms+ depending on corpus size and hardware.",
    },
  };

  console.log(JSON.stringify(output, null, 2));
}

main().catch(err => {
  console.error("Benchmark failed:", err);
  process.exit(1);
});
