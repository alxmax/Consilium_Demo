---
milestone: v1.1
id: CONSILIUM-TRIAS-HAIKU-SCHEMA-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001, CONSILIUM-MODE-TRIAS-001]
risk: 1
---

# trias-model-assignment

> Trias uniform model assignment: all 3 personalities (pioneer, architect, steward) use sonnet. No per-personality schema workarounds needed.

## WHAT — Contract (normative)
- `scripts/personalities.py` shall expose a `PERSONALITIES` list where every entry carries a `model` field whose value controls which Claude model tier the Trias orchestrator dispatches for that sub-agent.
- Model assignments shall be uniform: pioneer → `sonnet`, architect → `sonnet`, steward → `sonnet`.
- No personality entry shall carry `schema_less: True`. All personalities use standard StructuredOutput dispatch.
- The `personalities.py` CLI shall emit a valid JSON array of exactly 3 objects, each with at minimum a `model` field, for use by the Trias orchestrator at runtime.

## WHAT — Verify intent
- None — all questions resolved.

## HOW — Acceptance (= tests)
- All three personalities emit a `model` field (test_model_fields_present).
- All assignments are sonnet (test_model_assignments, test_all_models_sonnet).
- No personality carries `schema_less` (test_no_schema_less_any_personality).
- CLI emits valid JSON array with `model` field on each entry (test_cli_output_valid_json).
