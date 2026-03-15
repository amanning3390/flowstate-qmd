# Hermes Hackathon 2026: FLOWSTATE-QMD
## Submission Writeup

**Repository:** [github.com/amanning3390/flowstate-qmd](https://github.com/amanning3390/flowstate-qmd)  
**Demo Video:** [assets/video/flowstate_demo.mp4](assets/video/flowstate_demo.mp4)  
**License:** MIT

---

### 1. Vision: The "No-Tool" Future

The primary bottleneck for AI agents today isn't reasoning—it's **latency**. Specifically, the "stutter" caused by the Retrieval-Augmented Generation (RAG) loop:

```
Traditional RAG:  user asks → agent decides to search → tool call → wait → process → answer
                              ↑_______________ 2-4 seconds of "stutter" _______________↑
```

**FLOWSTATE-QMD** is a drop-in upgrade for local agent memory (built on `@tobi/qmd`) that turns memory from a **tool** into an **intuition**:

```
FlowState:        user asks → context already loaded → agent answers immediately
                              ↑__ cache read only __↑
```

---

### 2. The Innovation: Anticipatory Caching

Instead of waiting for an agent to realize it's missing information, FLOWSTATE-QMD uses a background **session watcher**:

1. **Real-time Session Tracking** — Event-driven `fs.watch` monitors the agent's session log with 1500ms debouncing
2. **Context Vectorization** — Last 8KB of conversation context is embedded using Qwen3-Embedding-4B
3. **Anticipatory Pre-fetch** — Top-3 relevant memories are retrieved via `hybridQuery()` and cached to `~/.cache/qmd/intuition.json`
4. **Fast Injection** — Agent reads the JSON cache at turn start; context is already present

**Result:** When the cache is warm, the agent gets relevant project context from a file read instead of a full search round-trip.

---

### 3. Performance Benchmarks

**Full benchmark suite:** `bench/submission.ts` — Traditional RAG vs FlowState-QMD end-to-end comparison  
**Results saved:** `bench/submission-results.json` (programmatic) + `docs/BENCHMARKS.md` (human-readable)

**Summary (Apple M4, 24 GB RAM, 22 indexed documents, 20 rounds per scenario):**

| Metric | Traditional RAG | FlowState-QMD | Improvement |
|--------|----------------|---------------|-------------|
| Avg end-to-end latency | 404.7 ms | 0.009 ms | **44,146x faster** |
| Avg tool calls per question | 2.0 | 1.0 | **50% fewer** |
| Cache hit rate | N/A | 100% | — |
| Cache read latency | N/A | 0.009 ms | — |

**Per-scenario results:**

| Scenario | Traditional | FlowState | Speedup |
|----------|-------------|-----------|---------|
| ADR lookup (auth rollback) | 445 ms | 0.012 ms | 37,102x |
| Incident review | 362 ms | 0.009 ms | 40,224x |
| API design decision | 405 ms | 0.009 ms | 44,996x |
| Production runbook | 404 ms | 0.008 ms | 50,438x |

The bottleneck in Traditional RAG is not the search — it's the agent **deciding to search** (~200-600ms LLM reasoning). FlowState eliminates that decision entirely by pre-loading context.

All benchmarks are reproducible via `npx tsx bench/submission.ts`. See `docs/BENCHMARKS.md` for full methodology and detailed results.

**Hardware Profiles:**

| Profile | Models | VRAM | Use Case |
|---------|--------|------|----------|
| **Standard** | Qwen3-Embedding-4B + Qwen3-Reranker-4B | ~6GB | Full quality, Apple Silicon 16GB+ |
| **Lite** | Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B | ~1.2GB | Laptops, CI, low-memory systems |

When `liteMode` is enabled, `hybridQuery()` caps results at 5, limits candidates to 15, and **skips LLM reranking** — the most expensive step in the pipeline.

---

### 4. Technical Stack

- **Embedding Model:** `Qwen/Qwen3-Embedding-4B` (Q8_0 quantization, 4.3GB)
- **Reranker Model:** `QuantFactory/Qwen3-Reranker-4B` (Q4_0 quantization, 2.1GB)
- **Query Expansion:** SFT fine-tuned `qmd-query-expansion-1.7B` (GRPO exploration in progress — see `finetune/README.md`)
- **Inference Runtime:** `node-llama-cpp` with automatic Metal/CUDA/Vulkan detection
- **Store:** SQLite + FTS5 + `sqlite-vec` for hybrid BM25 + vector search
- **Fusion:** Reciprocal Rank Fusion (RRF) with learned weights

---

### 5. Multi-Agent Idempotency

FLOWSTATE-QMD solves the "Drunken Sailor" problem where multiple agents on the same host create redundant memories:

```
Agent A indexes: "The auth migration was rolled back due to connection pool exhaustion"
Agent B tries:   "Auth rollback happened because of DB connection issues"
                 ↓
QMD detects 0.94 similarity → Agent B annotates existing memory instead of duplicating
```

**Implementation** (`src/store.ts`):
- `checkDuplicateDocument()` computes cosine similarity against `vectors_vec` at index time
- **Threshold:** `DEDUP_SIMILARITY_THRESHOLD = 0.90` (configurable)
- **Scope:** Collection-level — only checks within the target collection
- **Tracking:** `getDedupStats()` returns `{ checked, deduped, inserted }` counters, surfaced in `qmd status`
- **Tests:** 10 integration tests in `test/idempotency.test.ts` using real SQLite + sqlite-vec

---

### 6. MCP Integration

Five tools exposed via Model Context Protocol:

| Tool | Purpose |
|------|---------|
| `fetch_anticipatory_context` | Read pre-cached memories (cache read) or fall back to live search |
| `query` | Hybrid search with lex/vec/hyde modes |
| `get` | Retrieve single document by path or docid |
| `multi_get` | Batch retrieve by glob or comma-separated list |
| `status` | Index health, stats, FlowState telemetry, and dedup stats |

**Supported Agent Wrappers (8 targets):**
- Hermes Agent (`~/.hermes/config.yaml`)
- Claude Code (`~/.claude.json`)
- Codex CLI (`~/.codex/config.toml`)
- Gemini CLI (`~/.gemini/settings.json`)
- Kiro (`.kiro/settings/mcp.json`)
- VS Code (`.vscode/mcp.json`)
- OpenClaw (`.openclaw/config.json`)
- pi (`.pi/settings.json`)

---

### 7. Cache Telemetry

FlowState tracks cache performance in `~/.cache/qmd/telemetry.json`:

```json
{
  "cacheHits": 47,
  "cacheMisses": 12,
  "totalRefreshes": 35,
  "avgRefreshMs": 180.5,
  "lastHitAt": "2026-03-15T10:30:00Z",
  "lastMissAt": "2026-03-15T09:15:00Z"
}
```

Telemetry is surfaced via `qmd status` and the MCP `status` tool.

---

### 8. Test Coverage

```
Test Files:  19 passed (19)
Tests:       736 passed | 66 skipped (802 total)
```

Key test suites:
- `idempotency.test.ts` — 10 tests: cosine dedup with real SQLite + sqlite-vec
- `flow.engine.test.ts` — 16 tests: anticipatory cache lifecycle and telemetry
- `mcp.test.ts` — All 5 MCP tools
- `store.test.ts` — Hybrid search, RRF fusion, chunking
- `eval.test.ts` — Hit@K retrieval quality metrics
- `cli.test.ts` — Full E2E tests spawning child processes

---

### 9. Before/After Comparison

**Before (Traditional RAG):**
```
User: "Why did we revert the auth migration?"
Agent: [thinking...] I should search for this.
Agent: [tool_call: search("auth migration revert")]
       ... search + rerank round-trip ...
Agent: [processes results]
Agent: "Based on the changelog, the auth migration was reverted because..."
```

**After (FlowState-QMD):**
```
User: "Why did we revert the auth migration?"
Agent: [reads intuition.json — cache hit, relevant docs already present]
Agent: "Based on the changelog entry from March 3rd, the auth migration was 
        reverted due to connection pool exhaustion under load. ADR-017 documents
        the decision to use a phased rollout instead."
```

---

### 10. What We Built (Hackathon Contribution)

This project is an evolution of [`@tobi/qmd`](https://github.com/tobi/qmd) by Tobi Lütke. We chose to build on QMD because its local-first, SQLite-Vec-based architecture is the gold standard for high-performance terminal search.

**New code added for this hackathon:**
- `src/flow/engine.ts` (352 lines) — FlowState anticipatory cache engine with telemetry
- `src/bootstrap.ts` (683 lines) — Multi-agent bootstrap system for 8 wrapper targets
- `src/store.ts` additions (~80 lines) — Idempotency layer with cosine dedup + lite mode wiring
- `src/embedded-skills.ts` (248 lines) — Packaged agent skill embedding
- `src/mcp/server.ts` additions (~100 lines) — `fetch_anticipatory_context` tool + telemetry in status
- `bench/` (5 files) — Reproducible benchmark scripts including `full-bench.ts` with real results
- `test/idempotency.test.ts` (10 tests) — Idempotency integration tests
- `test/flow.engine.test.ts` (16 tests) — Telemetry and cache lifecycle tests
- `finetune/` — SFT fine-tuning pipeline for query expansion model
- `assets/video/` — Hackathon video generation

---

**"Why ask when your agent already knows?"**

Submitted by Adam Manning for the Hermes Hackathon 2026.
