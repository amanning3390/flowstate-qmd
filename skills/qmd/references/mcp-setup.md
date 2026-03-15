# FlowState-QMD MCP Setup

## Install

```bash
npm install -g @tobilu/qmd
qmd collection add ~/path/to/repo/docs --name docs
qmd collection add ~/path/to/repo/notes --name notes
qmd embed
```

## Canonical Agent Setup

The default MCP server name is `qmd`.

**Hermes Agent** (`~/.hermes/config.yaml`):
```yaml
mcp_servers:
  qmd:
    command: qmd
    args:
      - mcp
```

**Claude Code** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
```

**Codex-style local agents**

Use the same stdio server:

```json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.qmd]
command = "qmd"
args = ["mcp"]
```

**Gemini CLI** (`~/.gemini/settings.json`), **Kiro** (`.kiro/settings/mcp.json`), and **VS Code** (`.vscode/mcp.json`) all use the same canonical `qmd` server definition. `qmd init --target all` will emit or install the right config automatically.

## Bootstrap

```bash
qmd init --target hermes
qmd init --target all
qmd doctor --json
```

`qmd init` keeps one shared contract across Hermes, Claude Code, Codex, Gemini CLI, Kiro, VS Code, OpenClaw, and pi:

1. `fetch_anticipatory_context`
2. `query`
3. `get` / `multi_get`
4. `status`

## HTTP Mode

```bash
qmd mcp --http              # Port 8181
qmd mcp --http --daemon     # Background daemon
qmd mcp stop                # Stop daemon
```

## Tool Order For Coding Agents

1. `fetch_anticipatory_context` for the current turn
2. `query` for deeper retrieval
3. `get` / `multi_get` for exact evidence
4. `status` when setup or freshness looks wrong

## Example Query Payload

```json
{
  "searches": [
    { "type": "lex", "query": "\"database migration\" rollback" },
    { "type": "vec", "query": "why did the migration rollback and what changed afterward?" }
  ],
  "collections": ["docs", "notes"],
  "intent": "coding agent memory for release debugging",
  "limit": 6
}
```

## Troubleshooting

- Not starting: `which qmd`, then run `qmd mcp` manually
- No useful results: `qmd collection list`, `qmd embed`, `qmd status`
- No anticipatory context: ensure FlowState is writing `~/.cache/qmd/intuition.json`
- Slow first search: normal local model warmup
