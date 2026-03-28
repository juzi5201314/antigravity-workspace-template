# Graph Retrieval Skill

## Purpose
Expose graph-based retrieval as a tool capability without breaking the
existing Antigravity execution chain.

## Tool
- `query_graph(query, max_hops=2, workspace='.')`

## Behavior
- Reads normalized graph store files under `.antigravity/graph/`.
- Builds a query-relevant subgraph.
- Returns LLM-friendly semantic triples plus replayable evidence metadata.

## Output Contract
```json
{
  "summary": "...",
  "triples": [["subject", "predicate", "object"]],
  "evidence": [{"retrieval_id": "...", "tool_name": "..."}],
  "nodes": [...],
  "edges": [...]
}
```

## Design Notes
- Keeps tool-driven and replayable architecture.
- Does not bypass pipeline.
- Intended for structure/dependency questions and context enrichment.
