/**
 * Benchmark: search latency across FTS, vector, and hybrid pipelines.
 *
 * Usage:
 *   bun bench/latency.ts
 *
 * Requires an indexed database at ~/.cache/qmd/index.sqlite (or INDEX_PATH).
 */

import { createStore, searchFTS, hybridQuery } from "../src/store.js";

const WARMUP_ROUNDS = 2;
const BENCH_ROUNDS = 10;
const QUERIES = [
  "authentication middleware",
  "database migration rollback",
  "API rate limiting",
];

type BenchResult = {
  name: string;
  query: string;
  rounds: number;
  minMs: number;
  maxMs: number;
  avgMs: number;
  p50Ms: number;
  p95Ms: number;
};

function percentile(sorted: number[], p: number): number {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)]!;
}

async function benchmarkFTS(store: ReturnType<typeof createStore>, query: string): Promise<BenchResult> {
  // Warmup
  for (let i = 0; i < WARMUP_ROUNDS; i++) {
    store.searchFTS(query, 10);
  }

  const timings: number[] = [];
  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    store.searchFTS(query, 10);
    timings.push(performance.now() - start);
  }

  timings.sort((a, b) => a - b);
  return {
    name: "FTS (BM25)",
    query,
    rounds: BENCH_ROUNDS,
    minMs: Math.round(timings[0]! * 100) / 100,
    maxMs: Math.round(timings[timings.length - 1]! * 100) / 100,
    avgMs: Math.round((timings.reduce((a, b) => a + b, 0) / timings.length) * 100) / 100,
    p50Ms: Math.round(percentile(timings, 50) * 100) / 100,
    p95Ms: Math.round(percentile(timings, 95) * 100) / 100,
  };
}

async function benchmarkHybrid(store: ReturnType<typeof createStore>, query: string, liteMode: boolean): Promise<BenchResult> {
  // Warmup
  for (let i = 0; i < WARMUP_ROUNDS; i++) {
    await hybridQuery(store, query, { limit: 5, liteMode });
  }

  const timings: number[] = [];
  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    await hybridQuery(store, query, { limit: 5, liteMode });
    timings.push(performance.now() - start);
  }

  timings.sort((a, b) => a - b);
  const label = liteMode ? "Hybrid (lite)" : "Hybrid (full)";
  return {
    name: label,
    query,
    rounds: BENCH_ROUNDS,
    minMs: Math.round(timings[0]! * 100) / 100,
    maxMs: Math.round(timings[timings.length - 1]! * 100) / 100,
    avgMs: Math.round((timings.reduce((a, b) => a + b, 0) / timings.length) * 100) / 100,
    p50Ms: Math.round(percentile(timings, 50) * 100) / 100,
    p95Ms: Math.round(percentile(timings, 95) * 100) / 100,
  };
}

async function main(): Promise<void> {
  const store = createStore();
  const results: BenchResult[] = [];

  for (const query of QUERIES) {
    results.push(await benchmarkFTS(store, query));
    results.push(await benchmarkHybrid(store, query, false));
    results.push(await benchmarkHybrid(store, query, true));
  }

  store.close();

  // Output as JSON for programmatic consumption
  const output = {
    timestamp: new Date().toISOString(),
    rounds: BENCH_ROUNDS,
    warmup: WARMUP_ROUNDS,
    results,
  };

  console.log(JSON.stringify(output, null, 2));
}

main().catch((err) => {
  console.error("Benchmark failed:", err);
  process.exit(1);
});
