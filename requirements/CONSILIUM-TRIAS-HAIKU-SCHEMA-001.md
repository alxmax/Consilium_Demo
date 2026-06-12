---
milestone: v1.1
id: CONSILIUM-TRIAS-HAIKU-SCHEMA-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001, CONSILIUM-MODE-TRIAS-001]
risk: 1
---

# trias-haiku-schema

> Trias model-diversity assignment: per-personality model fields (pioneer=haiku, architect=sonnet, steward=opus) with schema-less Steward dispatch and Pioneer circuit-breaker.

## WHAT — Contract (normative)
- `scripts/personalities.py` shall expose a `PERSONALITIES` list where every entry carries a `model` field whose value controls which Claude model tier the Trias orchestrator dispatches for that sub-agent.
- Model assignments shall be fixed: pioneer → `haiku`, architect → `sonnet`, steward → `opus`.
- The Steward entry shall carry `schema_less: True`. Pioneer and Architect shall not carry this field (or carry it as falsy). This flag signals to the orchestrator that Steward must be dispatched without a StructuredOutput schema; Steward returns fenced JSON and the orchestrator parses it with `json.loads()`. Rationale: Opus+StructuredOutput tool calls are unreliable and may silently skip the call.
- Pioneer shall have an implicit circuit-breaker: when Pioneer (Haiku) returns malformed or empty JSON, the orchestrator substitutes `model: sonnet` and re-dispatches that personality once. On second failure, Pioneer is treated as a non-vote per B2 timeout rules. Non-pioneer personalities have no fallback — they are counted as a non-vote on first failure.
- The `personalities.py` CLI shall emit a valid JSON array of exactly 3 objects, each with at minimum a `model` field, for use by the Trias orchestrator at runtime.

## WHAT — Verify intent
- None — all questions resolved.

## HOW — Acceptance (= tests)
- All three personalities emit a `model` field (test_model_fields_present).
- Assignments are exactly pioneer=haiku, architect=sonnet, steward=opus (test_model_assignments).
- Steward has `schema_less=True`; Pioneer and Architect do not (test_steward_schema_less, test_pioneer_and_architect_not_schema_less).
- Pioneer circuit-breaker returns `"sonnet"` as fallback; non-pioneer personalities return their own model unchanged (test_circuit_breaker).
- CLI emits valid JSON array with `model` field on each entry (test_cli_output_valid_json).
