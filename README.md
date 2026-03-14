# FLOWSTATE-QMD
### Anticipatory Memory for AI Agents
#### Hermes 2026 Hackathon Entry

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Hermes](https://img.shields.io/badge/Powered%20by-Hermes%20Agent-blueviolet)](https://github.com/NousResearch/hermes-agent)
[![Base: QMD](https://img.shields.io/badge/Base-tobi%2Fqmd-blue)](https://github.com/tobi/qmd)

```text
  _______  _        _______           _______ _________ _______ _________ _______ 
 (  ____ \( \      (  ___  )|\     /|(  ____ \__   __/(  ___  )\__   __/(  ____ \
 | (    \/| (      | (   ) || )   ( || (    \/   ) (   | (   ) |   ) (   | (    \/
 | (__    | |      | |   | || | _ | || (_____    | |   | (___) |   | |   | (__    
 |  __)   | |      | |   | || |( )| |(_____  )   | |   |  ___  |   | |   |  __)   
 | (      | |      | |   | || || || |      ) |   | |   | (   ) |   | |   | (      
 | )      | (____/\| (___) || () () |/\____) |   | |   | )   ( |   | |   | (____/\
 |/       (_______/(_______)(_______)\_______)   )_(   |/     \|   )_(   (_______/
                                                                                  
  _______  _______  ______                                                       
 (  ___  )(       )(  __  \                                                      
 | (   ) || () () || (  \  )                                                     
 | |   | || || || || |   ) |                                                     
 | |   | || |(_)| || |   | |                                                     
 | |   | || |   | || |   ) |                                                     
 | (___) || )   ( || (__/  )                                                     
 (_______)|/     \|(______/                                                      
```

---

## THE PROBLEM: The Stutter Loop

Every AI agent using traditional RAG suffers from the same fundamental flaw — what we call the **Stutter Loop**:

```
User: "What were the results from last week's experiment?"
Agent: *thinks* → "I need to search for that..."
Agent: *calls search tool* → waiting...
Agent: *receives results* → processing...
Agent: "Based on the search results..."
```

That pause. That hesitation. That stutter. It breaks the illusion of intelligence and wastes precious seconds on every knowledge-dependent response.

## THE SOLUTION: Anticipatory Memory

**FlowState-QMD** eliminates the stutter loop entirely. Instead of waiting for the agent to realize it needs context, we **pre-fetch relevant memories before the agent even begins its turn**.

```
User: "What were the results from last week's experiment?"
Agent: *already knows* → "The Q3 benchmark showed a 23% improvement..."
```

The agent doesn't search. The agent **already knows**. We call this **Intuition**.

---

## ARCHITECTURE

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLOWSTATE-QMD ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐    │
│   │ Agent Session│────▶│   Flow Engine    │────▶│  Intuition      │    │
│   │   Log File   │     │  (Background)    │     │  Cache (JSON)   │    │
│   └──────────────┘     └────────┬─────────┘     └────────┬────────┘    │
│        tail -f                  │                         │             │
│        ~1.5s debounce           │                         │             │
│                                 ▼                         ▼             │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                        QMD Core Engine                           │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │  │
│   │  │  Index   │  │  Search  │  │  Embed   │  │  Rerank         │  │  │
│   │  │ (SQLite) │  │ (Hybrid) │  │ (Qwen3)  │  │  (Qwen3)        │  │  │
│   │  └──────────┘  └──────────┘  └──────────┘  └─────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                       │
│            ┌────────────────────┼────────────────────┐                  │
│            ▼                    ▼                    ▼                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │  SQLite +    │    │  MCP Server  │    │   CLI Tool   │             │
│   │  sqlite-vec  │    │ (stdio/HTTP) │    │    (qmd)     │             │
│   └──────────────┘    └──────────────┘    └──────────────┘             │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                  Hermes Agent Integration                        │  │
│   │  • Embedded skill checks ~/.cache/qmd/intuition.json            │  │
│   │  • Pre-fetched context injected into system prompt              │  │
│   │  • Zero tool-call latency — agent "already knows"               │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Flow Engine (`src/flow/engine.ts`)
The heart of FlowState. A background process that:
- **Watches** the active agent session log using `fs.watchFile` (resilient to rotations)
- **Debounces** updates (1500ms) to avoid redundant processing
- **Vectorizes** the last 2KB of conversation context
- **Queries** the QMD store for relevant memories (top-3, minScore=0.4)
- **Writes** results to `~/.cache/qmd/intuition.json`
- Handles file rotation, truncation, and graceful shutdown

#### 2. Intuition Cache (`~/.cache/qmd/intuition.json`)
A lightweight JSON file containing the top-3 most relevant memories:
```json
{
  "timestamp": 1741972800000,
  "context": "last 2KB of conversation",
  "results": [
    {
      "path": "qmd://notes/project-plan.md",
      "score": 0.87,
      "snippet": "The Q3 benchmark showed..."
    }
  ]
}
```

#### 3. Hermes Embedded Skill (`src/embedded-skills.ts`)
Base64-encoded skill files that teach Hermes to:
- Check the intuition cache at turn start
- Inject pre-fetched context into the system prompt
- Operate with zero tool-call overhead

#### 4. QMD Search Engine (from tobi/qmd)
The mature foundation we build on:
- **Hybrid Search**: BM25 (FTS5) + Vector (sqlite-vec) + Reciprocal Rank Fusion
- **Smart Chunking**: Structure-aware splitting (headings > code blocks > paragraphs)
- **Query Expansion**: LLM-powered query variants (lex/vec/hyde)
- **Intent-Aware Pipeline**: All 5 search stages respect intent parameter
- **Strong Signal Bypass**: Skip expensive LLM when BM25 has a clear winner

---

## TECHNICAL SPECIFICATIONS

### Models

| Component | Model (Standard) | Model (Lite) | Purpose |
|-----------|------------------|--------------|---------|
| Embeddings | Qwen3-Embedding-4B (Q8_0 GGUF, 4.2GB) | bge-micro-v2-GGUF (~800MB) | Document & query vectorization |
| Reranking | Qwen3-Reranker-4B (Q4_0 GGUF, 2.4GB) | jina-reranker-v1-tiny-en-GGUF (~300MB) | Result relevance scoring |
| Query Expansion | qmd-query-expansion-1.7B (1.0GB) | (Optional, skips if low latency) | GRPO-trained query variants |

### Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Node.js >= 22 / Bun |
| Language | TypeScript |
| Database | SQLite via better-sqlite3 / bun:sqlite |
| Vector Index | sqlite-vec (native, in-process) |
| LLM Runtime | node-llama-cpp (GGUF inference) |
| Protocol | MCP (Model Context Protocol) SDK |
| Testing | Vitest (646 tests passing) |

### Performance

| Metric | Standard (4B) | Lite (~0.8B) | 
|--------|---------------|--------------|
| Intuition Cache Read | < 50ms (disk I/O) | < 50ms (disk I/O) |
| Model VRAM Usage | ~6.5GB | ~1.2GB |
| Flow Engine Cycle | ~2-3s (debounced) | ~1.5s (faster inference) |
| BM25 Search | < 10ms | < 10ms |
| Vector Search (top-10) | < 50ms | < 20ms |
| Full Hybrid + Rerank | < 500ms | < 200ms |
| Apple Silicon Support | M2 Pro+ / 16GB+ RAM | M1/M2/M3 all supported (8GB RAM) |

---

## KEY INNOVATIONS

### 1. Anticipatory vs. Reactive Retrieval
Traditional RAG is reactive — the agent must decide to search. FlowState is anticipatory — context is prepared before it's needed. This is a paradigm shift from "pull" to "push" memory.

### 2. Zero-Latency Context Injection
By writing to a JSON cache and using an embedded Hermes skill, context appears in the system prompt with no tool call overhead. The agent doesn't "search" — it "remembers."

### 3. Multi-Agent Memory Pool
The SQLite + sqlite-vec database is a shared, non-redundant memory store. Hermes, Claude Code, and all sub-agents access the same pool — no duplicate indexing, no sync issues.

### 4. Local-First Privacy
All models run locally via GGUF/node-llama-cpp. Zero API calls, zero cloud dependencies. Your data never leaves your machine.

### 5. GRPO Fine-Tuned Query Expansion
Custom model trained with Group Relative Policy Optimization for better named entity preservation and format compliance in query expansion.

### 6. Smart Chunking
Scored break-point detection that respects markdown structure:
- Headings (score: 10) > Code blocks (score: 8) > Paragraph breaks (score: 5) > Newlines (score: 1)
- 900 tokens per chunk with 15% overlap
- Never splits inside code fences

### 7. Intent-Aware Pipeline
The `intent` parameter steers all five search pipeline stages without searching on its own:
- Query expansion variant selection
- Strong-signal bypass threshold
- Chunk selection strategy
- Reranking aggressiveness
- Snippet extraction style

---

## INSTALLATION

### Prerequisites
- Node.js >= 22 or Bun
- macOS (Apple Silicon recommended) or Linux
- ~8GB disk space for models

### Setup

```bash
# Clone the repository
git clone https://github.com/amanning3390/flowstate-qmd.git
cd flowstate-qmd

# Install dependencies
bun install

# Download models (Qwen3-Embedding-4B and Qwen3-Reranker-4B)
qmd pull

# Initialize a collection
qmd init

# Index your documents
qmd index ./my-documents
```

### Running the Flow Engine

```bash
# Start the flow engine with your agent session log
qmd flow start --watch ~/.hermes/sessions/current.log

# Or use the MCP server with daemon mode
qmd mcp --daemon --port 8080
```

### Hermes Integration

```bash
# Configure Hermes to use FlowState
# Add to your Hermes config:
cat >> ~/.hermes/config.yaml << 'EOF'
memory:
  provider: qmd
  intuition_cache: ~/.cache/qmd/intuition.json
EOF
```

---

## USAGE EXAMPLES

### CLI Search

```bash
# Basic search
qmd search "deployment procedures"

# Search with JSON output
qmd search --json "API authentication"

# Search with intent
qmd search --intent code "error handling patterns"

# List collections
qmd collection list

# Get document by virtual path
qmd get qmd://notes/project-plan.md
```

### MCP Server

```bash
# Start MCP server (stdio)
qmd mcp

# Start MCP server (HTTP daemon)
qmd mcp --daemon --port 8080

# Stop daemon
qmd mcp stop
```

### Programmatic API

```typescript
import { QMDStore } from '@tobilu/qmd';

const store = new QMDStore({
  dbPath: './data/qmd.db',
  embeddingModel: 'qwen3-embedding-4b',
  rerankerModel: 'qwen3-reranker-4b'
});

// Index documents
await store.index('./my-documents');

// Search with hybrid retrieval
const results = await store.search('deployment procedures', {
  limit: 10,
  rerank: true,
  intent: 'factual'
});
```

---

## PROJECT STRUCTURE

```
flowstate-qmd/
├── src/
│   ├── index.ts              # SDK public API
│   ├── store.ts              # Core data access, search, chunking
│   ├── llm.ts                # LLM abstraction, embeddings, reranking
│   ├── db.ts                 # Cross-runtime SQLite layer
│   ├── collections.ts        # YAML config management
│   ├── maintenance.ts        # DB cleanup operations
│   ├── embedded-skills.ts    # Base64-encoded Hermes skill files
│   ├── flow/
│   │   └── engine.ts         # Anticipatory retrieval engine
│   ├── cli/
│   │   ├── qmd.ts            # CLI implementation
│   │   └── formatter.ts      # Output formatting
│   └── mcp/
│       └── server.ts         # MCP server implementation
├── test/                     # 20+ test files (646 passing)
├── bin/qmd                   # Entry point wrapper
├── package.json
├── CHANGELOG.md              # Version history
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## TESTING

```bash
# Run all tests
bun test

# Run specific test file
bun test test/flow.engine.test.ts

# Run with LLM integration tests (requires models)
QMD_RUN_LLM_TESTS=1 bun test
```

**Test Coverage:** 646 tests passing, 66 skipped (LLM integration gated behind env var)

---

## CREDITS & ACKNOWLEDGMENTS

### Original Project: QMD by Tobi Lütke

FlowState-QMD is built on top of [QMD (Query Markup Documents)](https://github.com/tobi/qmd) by [Tobi Lütke](https://github.com/tobi) (CEO of Shopify). QMD provided the rock-solid foundation of:

- SQLite + sqlite-vec vector storage
- Hybrid search (BM25 + vector + reranking)
- Smart markdown chunking
- MCP server implementation
- CLI tooling
- Query expansion pipeline

Without QMD's mature, production-grade search engine, FlowState would not exist. Our contribution is the **anticipatory retrieval layer** — the Flow Engine and Intuition Cache — that transforms QMD from a reactive search tool into a proactive memory system for AI agents.

### Built With

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — The AI agent framework this integrates with
- [node-llama-cpp](https://github.com/withcatai/node-llama-cpp) — Local GGUF model inference
- [sqlite-vec](https://github.com/asg017/sqlite-vec) — Vector similarity search for SQLite
- [Model Context Protocol](https://modelcontextprotocol.io/) — Standard protocol for AI tool integration

### Special Thanks

- **Nous Research** for organizing the Hermes Hackathon 2026
- **Tobi Lütke** for creating QMD and open-sourcing it
- The open-source community for the incredible tools that made this possible

---

## LICENSE

MIT License

Copyright (c) 2026 Adam Manning

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

<p align="center">
  <b>Built with 💜 for the Hermes Hackathon 2026</b><br>
  <i>"Why ask when your agent already knows?"</i>
</p>
