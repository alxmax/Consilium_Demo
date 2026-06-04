---
id: CONSILIUM-TRACE-GRAPH-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# trace_graph

> Renders a per-run Mermaid flowchart of what actually executed in the deliberation pipeline.

## Input
- stdin (default) or `--input <path>`: a canonical run JSON file from `.consilium/runs/`
- `--fence`: boolean flag, wraps output in a ```mermaid code fence

## Description
Renders a per-run view of the deliberation pipeline as a Mermaid flowchart. It reads a canonical run JSON and emits a mode-aware directed graph showing what actually executed for that run: scope-gate skips, prior-deliberation passthroughs, Conservator `scale_down` short-circuits, the Trias fan of three parallel personality sub-agents, or the standard sequential/dialectic voice chain with optional Skeptic advisory. This complements the static architecture diagram in `docs/architecture/src/pipeline.jsx` with a concrete, inspectable trace per run. The output is valid Mermaid and renders natively in GitHub markdown and at mermaid.live without any additional toolchain.

## Output
- Mermaid flowchart text to stdout (plain or fenced in ```mermaid when `--fence` is set)
- exit code 0 on success; 2 on malformed JSON or missing/unreadable input

## WHAT — Verify intent (open questions for the human)
- A 'prior-deliberation passthrough run produces a two-node graph `PRIOR -> REP`' — but a passthrough run may still have metadata (confidence, chosen approach) worth showing; is the two-node minimal graph intentional, or should it show the passthrough's source run reference?
- For a sequential run with a Skeptic, the graph shows 'an advisory edge from AGG to SKP and from SKP to REP' — but when the Skeptic overrides the chosen candidate (`--skeptic-can-override`), should the edge semantics change (e.g., a different edge label or a direct replacement edge)?
- The output is described as 'valid Mermaid' — is there a validation step in the acceptance test, or is correctness only confirmed by visual inspection at mermaid.live?

## Acceptance (= tests)
- A run with `skipped=true` produces a flowchart containing only a SKIP node with the skip reason.
- A Trias run produces a flowchart with ROOT, PIO, ARC, STE, and VOTE nodes with edges from ROOT to each personality and from each personality to VOTE.
- A sequential run with a skeptic voice in the deliberation log produces an advisory edge from AGG to SKP and from SKP to REP.
- A prior-deliberation passthrough run produces a two-node graph `PRIOR -> REP`.
- Running with `--fence` wraps the Mermaid output in triple-backtick mermaid fences.
