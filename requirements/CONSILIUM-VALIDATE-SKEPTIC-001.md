---
milestone: v1.1
id: CONSILIUM-VALIDATE-SKEPTIC-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-VOICE-SKEPTIC-001, CONSILIUM-UTILS-001]
risk: 2
---

# validate_skeptic

> Describes observed behavior, verified against scripts/validate_skeptic.py source.

## Input
- A Skeptic voice output JSON on stdin (produced by the Skeptic voice per `prompts/voices/skeptic.md`)

## Description
Structural validation gate for Skeptic output. Enforces the machine-checkable
subset of the gate described in `prompts/voices/skeptic.md` and
`modes/skeptic_on_chosen.md` — shape and evidence rules only, not semantic
correctness. A verdict that fails this gate is discarded and the original
`chosen` is shipped unchallenged.

Rules enforced:
- `can_object` must be a bool
- `can_object=false` → `objection` must be null/absent
- `can_object=true` → `objection` is an object with:
  - `concrete_concerns`: list of strings; `quoted_scenario`: str or null
  - Evidence gate: ≥2 non-empty `concrete_concerns` OR a non-empty `quoted_scenario`
  - `failure_mode` in `{correctness, goal_fit, verification_inadequate, meta_scope_mismatch}`
  - `addressable` in `{in_place, requires_redesign, unaddressable}`
  - `failure_mode=goal_fit` → at least one `concrete_concern` references `"success_criterion"`

## Output
- Exit 0 — verdict is well-formed; orchestrator may apply it
- Exit 1 — invalid; each problem printed to stderr; orchestrator ships original chosen
- Exit 2 — malformed JSON input

## WHAT — Verify intent
- None — all questions resolved.

## WHAT — Contract
- Shall validate `can_object` as a bool; exit 1 if missing or non-bool.
- `can_object=false` shall require `objection` null or absent; presence of a non-null `objection` is an error.
- `can_object=true` shall require `objection` with `concrete_concerns` (list) and `quoted_scenario` (str or null).
- Evidence gate shall reject if fewer than 2 non-empty `concrete_concerns` AND `quoted_scenario` is empty/null.
- `failure_mode` and `addressable` shall be validated against their allowed value sets.
- `failure_mode=goal_fit` shall require at least one `concrete_concern` containing the substring `"success_criterion"`.
- Shall exit 0 on valid, 1 on invalid (problems to stderr), 2 on malformed JSON.

## Acceptance (= tests)
- `can_object=false` with null objection exits 0
- `can_object=true` with ≥2 concrete_concerns exits 0
- `can_object=true` with only a non-empty quoted_scenario exits 0
- `can_object=true` with 0 concrete_concerns and null quoted_scenario exits 1 (evidence gate)
- `failure_mode=goal_fit` without "success_criterion" in any concern exits 1
- Unknown `failure_mode` value exits 1
- Malformed JSON exits 2
