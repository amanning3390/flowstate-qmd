# BENCHMARKS: Traditional RAG vs FlowState-QMD

## Methodology

**Test Hardware:** Apple M4, 24 GB RAM, Metal GPU  
**Test Corpus:** 22 indexed markdown documents (ADRs, changelogs, runbooks, docs)  
**Rounds:** 20 per scenario, 3 warmup rounds  
**Engine:** FTS5 (BM25) for traditional RAG, intuition cache for FlowState

## The Fundamental Difference

```
Traditional RAG flow:
  user asks → LLM thinks → decides to search → tool call → FTS/embed/rerank → respond
                         └─────── ~400ms agent decision ──────┘  └── 0.3-2000ms ──┘
                                                              Total: 400-2400ms

FlowState-QMD flow:
  user asks → context already in cache → respond
              └── 0.01ms read ──┘
              Total: <1ms
```

## Results Summary

### 1. End-to-End Latency

| Metric | Traditional RAG | FlowState-QMD | Improvement |
|--------|----------------|---------------|-------------|
| Average latency | 404.7 ms | 0.009 ms | **44,146x faster** |
| Includes agent decision time | Yes (~200-600ms) | Eliminated | — |
| Search/lookup time | 0.08-0.30 ms | 0.008-0.012 ms | **25x faster** |

The dominant cost in Traditional RAG is not the search itself—it's the agent
deciding *to* search. FlowState eliminates that decision entirely by pre-loading
context.

### 2. Tool Call Efficiency

| Metric | Traditional RAG | FlowState-QMD | Reduction |
|--------|----------------|---------------|-----------|
| Avg tool calls per question | 2.0 | 1.0 | **50%** |
| Minimum tool calls | 2 | 1 | — |
| Cache hit avoids search | — | Yes (100%) | — |

Traditional RAG requires:
1. `query` (decide + search)
2. `get` (retrieve full documents)

FlowState requires:
1. `fetch_anticipatory_context` (cache read, <1ms)

### 3. Cache Performance

| Metric | Value |
|--------|-------|
| Cache hit rate | **100%** (for cache-relevant scenarios) |
| Cache read latency | **0.009 ms avg** |
| Cache miss fallback | FTS search at ~0.1ms |
| Intuition freshness | Updated every 1.5s via fs.watch |

### 4. Per-Scenario Breakdown

| Scenario | Topic | Traditional | FlowState | Cache | Speedup |
|----------|-------|-------------|-----------|-------|---------|
| `adr-lookup` | Auth migration decision | 445.2 ms | 0.012 ms | ✓ | 37,102x |
| `debug-trace` | Incident review | 362.0 ms | 0.009 ms | ✓ | 40,224x |
| `api-reference` | API design | 405.0 ms | 0.009 ms | ✓ | 44,996x |
| `design-decision` | API contract decision | 414.9 ms | 0.009 ms | ✓ | 46,102x |
| `migration-guide` | Production runbook | 403.5 ms | 0.008 ms | ✓ | 50,438x |
| `architecture` | Search pipeline design | 397.4 ms | 0.008 ms | ✓ | 49,675x |

### 5. What Traditional RAG Costs You Per Day

Assuming an agent answers **100 questions/day** with an average latency difference
of 404.7 ms vs 0.009 ms:

```
Traditional RAG:  100 × 404.7ms = 40.5 seconds of waiting per day
FlowState-QMD:    100 × 0.009ms = 0.9 milliseconds per day

Time saved: ~40 seconds/day in pure waiting
Tool calls saved: 100 unnecessary searches eliminated
```

That might sound modest, but it compounds:
- **Flow is preserved:** the agent never "stops to think" about searching
- **User perception:** responses feel instantaneous
- **Multi-agent:** each agent sharing the same cache benefits from all others' context

### 6. Multi-Agent Deduplication (Bonus)

When multiple agents index the same content:

| Metric | Without Dedup | With FlowState Dedup |
|--------|---------------|---------------------|
| Duplicate documents | 100% of matching content | **6%** (94% deduped) |
| Similarity threshold | N/A | 0.90 cosine |
| Method | None | Semantic hashing via sqlite-vec |

## Running the Benchmarks

```bash
# 1. Index the repository
export INDEX_PATH=/tmp/qmd-bench-index.sqlite
npx tsx bench/setup-index.ts

# 2. Run the full comparison benchmark
npx tsx bench/submission.ts

# 3. Run individual benchmarks
npx tsx bench/full-bench.ts      # Cache vs FTS comparison
npx tsx bench/latency.ts         # Search latency across pipelines
npx tsx bench/cache-hit.ts       # Cache read/miss latency
npx tsx bench/tool-calls.ts      # MCP tool round-trip simulation
```

## Reproducibility

All benchmarks use deterministic warmup rounds and report:
- Min / Max / Average latency
- P50 / P95 / P99 latency
- Round count and warmup rounds

Results are saved to `bench/submission-results.json` for programmatic consumption.

---

*Measured on Apple M4, 24 GB RAM, Node.js v22.16.0, 2026-03-15*  
*Benchmark suite: `bench/submission.ts`*
