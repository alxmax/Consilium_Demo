---
milestone: v1.1
id: ARCH-CONSILIUM-REPORT-001
status: confirmed
level: architecture
layer: aggregate
depends_on: [CONSILIUM-AGGREGATOR-001, CONSILIUM-CONFIDENCE-001, CONSILIUM-BUILD-REPORT-001, CONSILIUM-VALIDATE-REPORT-001, CONSILIUM-VALIDATE-SKEPTIC-001, CONSILIUM-STRIP-CONTEXT-001, CONSILIUM-SCOPE-GATE-001, CONSILIUM-VOCABULARY-MAP-001, CONSILIUM-VERSION-001, CONSILIUM-UTILS-001]
satisfies: [SYS-CONSILIUM-VERDICT-001]
owner: alxmax
risk: 1
---

# Report pipeline: aggregate, score, assemble, validate

> The deterministic Python path that turns voice outputs into one canonical, validated report.

## Description

Every line in this section is binding.

- `strip_context.py` projects each voice's output to the fields the next voice needs, so later voices are not anchored by earlier reasoning. [[CONSILIUM-STRIP-CONTEXT-001]]
- `aggregator.py` picks the chosen candidate, `confidence.py` scores it, and `build_report.py` assembles the canonical report shape. [[CONSILIUM-AGGREGATOR-001]] [[CONSILIUM-CONFIDENCE-001]] [[CONSILIUM-BUILD-REPORT-001]]
- `validate_report.py` is the last gate before a report is written, and `validate_skeptic.py` gates the Skeptic's output. [[CONSILIUM-VALIDATE-REPORT-001]] [[CONSILIUM-VALIDATE-SKEPTIC-001]]
- `scope_gate.py` decides before any voice runs whether a change bypasses deliberation or needs explicit consent. [[CONSILIUM-SCOPE-GATE-001]]
- Shared paths, atomic writes, version stamps and value translations each have one home (`utils.py`, `version.py`, `vocabulary_map.py`). [[CONSILIUM-UTILS-001]] [[CONSILIUM-VERSION-001]] [[CONSILIUM-VOCABULARY-MAP-001]]

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given voice outputs from a Sequential run, when they flow through aggregator, confidence and build_report, then the result passes `validate_report.py`.
- **CASE-2** — Given a report missing `pipeline_executed`, when `validate_report.py` reads it, then it exits non-zero.
- **CASE-3** — Given a diff that the scope gate marks as needing consent, when `/consilium` runs, then no voice is dispatched before consent is given.
