/**
 * Benchmark: MCP tool call round-trip simulation.
 *
 * Usage:
 *   bun bench/tool-calls.ts
 *
 * Measures the overhead of constructing and parsing MCP tool responses,
 * simulating the work done by the MCP server for each tool invocation.
 */

import { createStore, hybridQuery } from "../src/store.js";
import { readIntuitionCache } from "../src/flow/engine.js";

const BENCH_ROUNDS = 20;
const WARMUP_ROUNDS = 3;

type ToolBenchResult = {
  tool: string;
  rounds: number;
  avgMs: number;
  p50Ms: number;
  p95Ms: number;
};

function percentile(sorted: number[], p: number): number {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)]!;
}

async function benchTool(
  name: string,
  fn: () => Promise<unknown> | unknown,
): Promise<ToolBenchResult> {
  // Warmup
  for (let i = 0; i < WARMUP_ROUNDS; i++) {
    await fn();
  }

  const timings: number[] = [];
  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    await fn();
    timings.push(performance.now() - start);
  }

  timings.sort((a, b) => a - b);
  return {
    tool: name,
    rounds: BENCH_ROUNDS,
    avgMs: Math.round((timings.reduce((a, b) => a + b, 0) / timings.length) * 100) / 100,
    p50Ms: Math.round(percentile(timings, 50) * 100) / 100,
    p95Ms: Math.round(percentile(timings, 95) * 100) / 100,
  };
}

async function main(): Promise<void> {
  const store = createStore();
  const results: ToolBenchResult[] = [];

  // Simulate "status" tool
  results.push(
    await benchTool("status", () => {
      return store.getStatus();
    }),
  );

  // Simulate "search" tool (FTS only)
  results.push(
    await benchTool("search (FTS)", () => {
      return store.searchFTS("authentication", 10);
    }),
  );

  // Simulate "query" tool (hybrid)
  results.push(
    await benchTool("query (hybrid)", async () => {
      return hybridQuery(store, "authentication middleware", {
        limit: 5,
        skipRerank: true,
      });
    }),
  );

  // Simulate "fetch_anticipatory_context" tool
  results.push(
    await benchTool("fetch_anticipatory_context", () => {
      return readIntuitionCache();
    }),
  );

  store.close();

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
