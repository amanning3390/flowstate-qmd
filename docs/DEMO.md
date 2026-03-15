# FlowState-QMD Demo Script

## Goal

Show that a coding agent can retrieve repo memory before it falls back to a reactive search loop.

## Setup

```bash
bun install
qmd pull
qmd collection add ./docs --name docs
qmd collection add ./notes --name notes
qmd collection add . --name repo-memory --mask 'CHANGELOG.md'
qmd embed
```

## Start Services

Terminal 1:

```bash
qmd mcp
```

Terminal 2:

```bash
qmd flow ~/.codex/sessions/current.log --lite
```

Compatibility alias:

```bash
qmd flow start --watch ~/.codex/sessions/current.log --lite
```

## Demo Narrative

1. Ask the coding agent a question that should hit project memory:
   - "Why did we revert the auth migration?"
   - "What did the ADR say about the rollback?"
   - "What changed after the incident review?"
2. Show the agent calling `fetch_anticipatory_context` first.
3. Show the returned memories already include the relevant ADR, changelog entry, or note.
4. Optionally call `query` to deepen or verify the evidence.
5. Use `get` or `multi_get` to open the exact supporting docs.

## Suggested Queries

```json
{
  "recent_conversation": "Why did we revert the auth migration and what changed afterward?",
  "refresh": false,
  "lite_mode": false
}
```

```json
{
  "searches": [
    { "type": "lex", "query": "\"auth rollback\" migration changelog" },
    { "type": "vec", "query": "why did we revert the authentication migration?" }
  ],
  "collections": ["docs", "notes"],
  "intent": "coding agent project memory for rollback debugging",
  "limit": 6
}
```

## What To Emphasize

- FlowState cache is warmed before the next turn.
- Memory is local-first and inspectable.
- The agent can show exact file paths, snippets, and document IDs.
- When cache is unavailable, the same MCP tool falls back to a live project-memory query.

## Safety Checks Before Presenting

```bash
npx vitest run --reporter=verbose test/
qmd status
```
