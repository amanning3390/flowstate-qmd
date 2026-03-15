// Generated from skills/qmd source files. Keep this in sync with the packaged skill content.

export type EmbeddedSkillFile = {
  relativePath: string;
  content: string;
};

const EMBEDDED_QMD_SKILL: Record<string, string> = {
  "SKILL.md": `---
name: qmd
description: FlowState-QMD gives coding agents anticipatory project memory over docs, notes, ADRs, changelogs, and runbooks.
license: MIT
compatibility: Requires the qmd CLI or MCP server. Install with qmd or npm, then connect agents via MCP.
metadata:
  author: Adam Manning and Tobi Lutke
  version: "2.0.1-flowstate"
allowed-tools: Bash(qmd:*), mcp__qmd__*
---

# QMD for Coding Agents

FlowState-QMD is a local-first memory layer for coding agents. It turns markdown knowledge bases into project memory that is fast enough to feel built in.

## What It Is Good At

- Repo memory: design docs, specs, ADRs, RFCs, changelogs
- Team memory: meeting notes, incident reviews, migration summaries
- Agent memory: anticipatory context before a reactive search step
- Trustworthy recall: inspectable snippets, doc IDs, and explain traces

## Status

!\`qmd status 2>/dev/null || echo "Not installed: run 'qmd skill install --global' or 'npm install -g @tobilu/qmd'"\`

## Start Here

1. Call \`fetch_anticipatory_context\` at the beginning of a coding turn when recent conversation context is available.
2. Use \`query\` when you need deeper retrieval or want to inspect the evidence directly.
3. Use \`get\` or \`multi_get\` to pull exact docs, ADRs, changelogs, or notes once you know what matters.

## MCP Tool: \`fetch_anticipatory_context\`

Use this first when you want the agent to feel like it already knows the project context.

\`\`\`json
{
  "recent_conversation": "What changed in the auth rollback plan and why did we revert the migration?",
  "refresh": false,
  "lite_mode": false
}
\`\`\`

Returns:
- cached anticipatory memories from FlowState when available
- or a fresh live query over the current project memory

## MCP Tool: \`query\`

\`\`\`json
{
  "searches": [
    { "type": "lex", "query": "\"auth rollback\" migration changelog" },
    { "type": "vec", "query": "why did we revert the authentication migration?" }
  ],
  "collections": ["docs", "notes"],
  "intent": "coding agent project memory for a migration debugging task",
  "limit": 8
}
\`\`\`

### Query Types

| Type | Method | Best for |
|------|--------|----------|
| \`lex\` | BM25 | exact names, code terms, filenames, changelog phrases |
| \`vec\` | Vector | natural-language engineering questions |
| \`hyde\` | Vector | nuanced answers when you know what the result should sound like |

### Writing Better Coding-Agent Queries

- Start with \`lex\` when you know a filename, subsystem, ADR title, or error string
- Add \`vec\` when you know the problem but not the vocabulary
- Add \`intent\` for ambiguous queries like "performance", "memory", or "rollback"
- Use \`--explain\` in the CLI when you need to understand why a memory was selected

## Other MCP Tools

| Tool | Use |
|------|-----|
| \`get\` | Retrieve a single document by path or \`#docid\` |
| \`multi_get\` | Pull several related documents by glob or list |
| \`status\` | Check collection health, embedding status, and defaults |

## CLI

\`\`\`bash
qmd collection add . --name repo-memory
qmd embed
qmd flow ~/.codex/sessions/current.log --lite
qmd query "why was the rollout reverted"
qmd query --json --explain "performance regression in auth service"
qmd get "#abc123"
qmd multi-get "docs/**/*.md,CHANGELOG.md"
\`\`\`

## Memory Model

- Durable knowledge: indexed markdown files in collections
- Working memory: FlowState anticipatory cache in \`~/.cache/qmd/intuition.json\`
- Context overlays: human-authored collection and path summaries via \`qmd context add\`

## Setup

\`\`\`bash
qmd skill install --global --yes
qmd collection add ~/projects/my-repo/docs --name docs
qmd collection add ~/projects/my-repo/notes --name notes
qmd embed
qmd mcp
\`\`\`
`,
  "references/mcp-setup.md": `# FlowState-QMD MCP Setup

## Install

\`\`\`bash
npm install -g @tobilu/qmd
qmd collection add ~/path/to/repo/docs --name docs
qmd collection add ~/path/to/repo/notes --name notes
qmd embed
\`\`\`

## Canonical Agent Setup

The default MCP server name is \`qmd\`.

**Hermes Agent** (\`~/.hermes/config.yaml\`):
\`\`\`yaml
mcp_servers:
  qmd:
    command: qmd
    args:
      - mcp
\`\`\`

**Claude Code** (\`~/.claude/settings.json\`):
\`\`\`json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
\`\`\`

**Claude Desktop** (\`~/Library/Application Support/Claude/claude_desktop_config.json\`):
\`\`\`json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
\`\`\`

**Codex-style local agents**

Use the same stdio server:

\`\`\`json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
\`\`\`

**Codex** (\`~/.codex/config.toml\`):
\`\`\`toml
[mcp_servers.qmd]
command = "qmd"
args = ["mcp"]
\`\`\`

**Gemini CLI** (\`~/.gemini/settings.json\`), **Kiro** (\`.kiro/settings/mcp.json\`), and **VS Code** (\`.vscode/mcp.json\`) all use the same canonical \`qmd\` server definition. \`qmd init --target all\` will emit or install the right config automatically.

## Bootstrap

\`\`\`bash
qmd init --target hermes
qmd init --target all
qmd doctor --json
\`\`\`

\`qmd init\` keeps one shared contract across Hermes, Claude Code, Codex, Gemini CLI, Kiro, VS Code, OpenClaw, and pi:

1. \`fetch_anticipatory_context\`
2. \`query\`
3. \`get\` / \`multi_get\`
4. \`status\`

## HTTP Mode

\`\`\`bash
qmd mcp --http              # Port 8181
qmd mcp --http --daemon     # Background daemon
qmd mcp stop                # Stop daemon
\`\`\`

## Tool Order For Coding Agents

1. \`fetch_anticipatory_context\` for the current turn
2. \`query\` for deeper retrieval
3. \`get\` / \`multi_get\` for exact evidence
4. \`status\` when setup or freshness looks wrong

## Example Query Payload

\`\`\`json
{
  "searches": [
    { "type": "lex", "query": "\"database migration\" rollback" },
    { "type": "vec", "query": "why did the migration rollback and what changed afterward?" }
  ],
  "collections": ["docs", "notes"],
  "intent": "coding agent memory for release debugging",
  "limit": 6
}
\`\`\`

## Troubleshooting

- Not starting: \`which qmd\`, then run \`qmd mcp\` manually
- No useful results: \`qmd collection list\`, \`qmd embed\`, \`qmd status\`
- No anticipatory context: ensure FlowState is writing \`~/.cache/qmd/intuition.json\`
- Slow first search: normal local model warmup
`,
};

export function getEmbeddedQmdSkillFiles(): EmbeddedSkillFile[] {
  return Object.entries(EMBEDDED_QMD_SKILL).map(([relativePath, content]) => ({
    relativePath,
    content,
  }));
}

export function getEmbeddedQmdSkillContent(): string {
  return EMBEDDED_QMD_SKILL["SKILL.md"]!;
}
