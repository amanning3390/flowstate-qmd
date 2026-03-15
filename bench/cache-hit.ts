/**
 * Benchmark: FlowState intuition cache hit rate and read latency.
 *
 * Usage:
 *   bun bench/cache-hit.ts
 *
 * Measures how fast the intuition cache can be read and parsed,
 * and simulates a series of cache reads to estimate real-world hit rates.
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const BENCH_ROUNDS = 1000;

type CacheBenchResult = {
  name: string;
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

function benchCacheRead(cachePath: string): CacheBenchResult {
  const timings: number[] = [];

  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    try {
      const raw = readFileSync(cachePath, "utf-8");
      JSON.parse(raw);
    } catch {
      // Cache miss or parse failure — still measure the latency
    }
    timings.push(performance.now() - start);
  }

  timings.sort((a, b) => a - b);
  return {
    name: "Cache read + parse",
    rounds: BENCH_ROUNDS,
    minMs: Math.round(timings[0]! * 1000) / 1000,
    maxMs: Math.round(timings[timings.length - 1]! * 1000) / 1000,
    avgMs: Math.round((timings.reduce((a, b) => a + b, 0) / timings.length) * 1000) / 1000,
    p50Ms: Math.round(percentile(timings, 50) * 1000) / 1000,
    p95Ms: Math.round(percentile(timings, 95) * 1000) / 1000,
  };
}

function benchCacheMiss(nonExistentPath: string): CacheBenchResult {
  const timings: number[] = [];

  for (let i = 0; i < BENCH_ROUNDS; i++) {
    const start = performance.now();
    existsSync(nonExistentPath);
    timings.push(performance.now() - start);
  }

  timings.sort((a, b) => a - b);
  return {
    name: "Cache miss (existsSync)",
    rounds: BENCH_ROUNDS,
    minMs: Math.round(timings[0]! * 1000) / 1000,
    maxMs: Math.round(timings[timings.length - 1]! * 1000) / 1000,
    avgMs: Math.round((timings.reduce((a, b) => a + b, 0) / timings.length) * 1000) / 1000,
    p50Ms: Math.round(percentile(timings, 50) * 1000) / 1000,
    p95Ms: Math.round(percentile(timings, 95) * 1000) / 1000,
  };
}

function main(): void {
  const cacheDir = join(homedir(), ".cache", "qmd");
  const cachePath = join(cacheDir, "intuition.json");
  const results: CacheBenchResult[] = [];

  // Ensure a cache file exists for the read benchmark
  const cacheExists = existsSync(cachePath);
  if (!cacheExists) {
    mkdirSync(cacheDir, { recursive: true });
    const synthetic = {
      timestamp: Date.now(),
      query: "benchmark test query for cache hit measurement",
      memories: [
        { file: "qmd://docs/bench.md", score: 0.85, title: "Benchmark doc" },
      ],
    };
    writeFileSync(cachePath, JSON.stringify(synthetic, null, 2));
  }

  results.push(benchCacheRead(cachePath));
  results.push(benchCacheMiss(join(cacheDir, "nonexistent-cache.json")));

  // Clean up synthetic cache if we created it
  if (!cacheExists) {
    try {
      const { unlinkSync } = require("fs");
      unlinkSync(cachePath);
    } catch {
      // ignore cleanup failure
    }
  }

  const output = {
    timestamp: new Date().toISOString(),
    rounds: BENCH_ROUNDS,
    results,
  };

  console.log(JSON.stringify(output, null, 2));
}

main();
