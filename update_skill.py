#!/usr/bin/env python3
import base64

# New skill content for FlowState-QMD
skill_content = """---
name: qmd-flowstate
description: FlowState-QMD - Anticipatory Memory for AI Agents. Eliminates the Stutter Loop by pre-fetching relevant context before the agent even asks.
license: MIT
compatibility: Requires FlowState-QMD MCP server running on localhost:8181.
metadata:
  author: Adam Manning
  version: \"1.0.0\"
allowed-tools: Bash(qmd:*), mcp__flowstate-qmd__*
---

# FlowState-QMD - Anticipatory Memory for AI Agents

Give your agent **anticipatory memory** - context that's ready before they even ask.

## Status

!`qmd status 2>/dev/null || echo "Not installed: run 'qmd init'"`

## MCP Tools

### `fetch_anticipatory_context`
The **primary tool** for FlowState. Call this at the start of every agent turn.

```json
{
  "recent_conversation": "What were the Q3 database migration results?",
  "lite_mode": false
}
```

Returns instant, predictive context based on current conversation state.

### `query`
Standard QMD search for when anticipatory context isn't enough.

## How It Works

1. **FlowEngine** runs in background, watching your agent's session log
2. **Anticipatory Memory** is pre-fetched based on conversation context  
3. **MCP Server** provides instant access via `fetch_anticipatory_context`
4. **Zero Latency** - agent already knows before asking

## Setup

```bash
# One-time setup
qmd init

# Start monitoring a session
qmd flow ~/.hermes/sessions/current.log --lite
```

## Performance

| Mode | Embedding Model | Reranker Model | VRAM Usage | Latency |
|------|-----------------|----------------|------------|---------|
| Standard | Qwen3-4B | Qwen3-4B | ~6.5GB | <500ms |
| Lite | bge-micro-v2 | jina-reranker-tiny | ~1.2GB | <200ms |

## For Agents

When you receive a user message:
1. Call `fetch_anticipatory_context` with the recent conversation
2. Inject the returned memories into your system prompt
3. Respond with **zero search latency**

## Architecture

```
User Message → Agent → fetch_anticipatory_context → FlowState-QMD MCP Server
                                                      ↓
                                           Anticipatory Memory (pre-fetched)
                                                      ↓
                                            Instant Context Injection
```

## Why This Wins

Traditional RAG: Agent → Realizes need → Searches → Waits → Responds (2-5s)
FlowState: Agent → Already has context → Responds (0ms)
"""

# Encode to base64
encoded = base64.b64encode(skill_content.encode('utf-8')).decode('utf-8')

# Format as TypeScript record entry
ts_entry = f'  \"SKILL.md\": \"{encoded}\",'

print("Base64 encoded skill (first 100 chars):", encoded[:100])
print("Length:", len(encoded))

# Write to a file for reference
with open('new_skill_content.txt', 'w') as f:
    f.write(skill_content)

with open('new_skill_base64.txt', 'w') as f:
    f.write(encoded)

print("\nFiles written: new_skill_content.txt, new_skill_base64.txt")
print("Update src/embedded-skills.ts with the new base64 string.")