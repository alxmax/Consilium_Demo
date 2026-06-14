---
id: CONSILIUM-VALIDATE-SKEPTIC-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-VOICE-SKEPTIC-001, CONSILIUM-UTILS-001]
risk: 1
---

# validate_skeptic

> Describes observed behavior, verified against scripts/validate_skeptic.py source.

## Input
- A Skeptic verdict JSON on stdin (produced by the Skeptic voice sub-agent)

## Description
Executable gate for the Skeptic validation rules documented in `prompts/voices/skeptic.md`.
Previously the gate was prose-only; this script enforces the machine-checkable subset so
a malformed or under-evidenced objection cannot pass unchecked into the orchestrator.

Checks enforced:
- `can_object` must be a bool
- `can_object=false` → `objection` must be null/absent (nothing to validate; ship original)
- `can_object=true` → `objection` is an object with:
  - `concrete_concerns`: list of strings; `quoted_scenario`: str or null
  - Evidence gate: ≥2 non-empty `concrete_concerns` OR a non-empty `quoted_scenario`
  - `failure_mode` in `{correctness, goal_fit, verification_inadequate, meta_scope_mismatch}`
  - `addressable` in `{in_place, requires_redesign, unaddressable}`
  - `failure_mode=goal_fit` → at least one `concrete_concern` references `"success_criterion"`
    (fabrication guard — skeptic.md mandates "success_criterion says X but chosen does Y")

NOT enforced (require semantic judgment): vagueness of concerns, whether cited constraints
appear in the actual success_criterion text, specificity of verification_inadequate scenarios.

## Output
- Exit 0 — verdict is valid
- Exit 1 — validation failed; each problem printed to stderr
- Exit 2 — malformed JSON input

## WHAT — Contract
- Shall validate `can_object` is a bool; reject any other type.
- Shall accept `can_object=false` with null/absent objection; reject if a populated objection is present.
- Shall enforce the evidence gate for `can_object=true`: ≥2 non-empty `concrete_concerns` OR a non-empty `quoted_scenario`; anything weaker exits 1.
- Shall validate `failure_mode` and `addressable` against their allowed value sets.
- Shall reject `failure_mode=goal_fit` objections where no `concrete_concern` contains `"success_criterion"`.
- Shall exit 0 on valid, 1 on validation failure (each problem on stderr), 2 on malformed JSON.

## WHAT — Verify intent
- None — all questions resolved.

## Acceptance (= tests)
- Well-formed verdict with 2 concrete concerns exits 0
- One concern + non-empty `quoted_scenario` exits 0
- `can_object=false` with null or missing objection exits 0
- `goal_fit` with a concern referencing `"success_criterion"` exits 0
- One concern + null scenario → exit 1 with "not enough evidence"
- `goal_fit` without a `"success_criterion"` reference → exit 1
- Unknown `failure_mode` → exit 1
- Unknown `addressable` → exit 1
- `can_object=true` with null objection → exit 1
- `can_object=false` with populated objection → exit 1
- Non-bool `can_object` → exit 1
- Non-dict input → exit 1

## WHERE — Current implementation
- scripts/validate_skeptic.py
<!-- implements: CONSILIUM-VALIDATE-SKEPTIC-001 -->
