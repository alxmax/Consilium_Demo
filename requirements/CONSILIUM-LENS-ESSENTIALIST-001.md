---
milestone: v1.1
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-ESSENTIALIST-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# essentialist lens

> WHY: generator-heavy member of the Trias personality team — biases all three voices toward first-principles minimalism: every component must earn its existence, deletion is the default, and the viable minimum is preferred over accretion.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to interrogate each component's right to exist and to prefer the viable-minimum candidate when candidates are otherwise comparable.
- The lens shall preserve each voice's standard structural role (Generator produces candidates, Control verifies correctness, Conservator assesses risk); it shifts perception and priority without suppressing the role's core output.
- When applied to Generator, the deletion bias shall order candidates smallest-first and always include a `do_nothing`/minimal candidate, while still producing the full 3-5 candidate spread — larger candidates are ranked lower, never censored.
- When applied to Conservator, the lens shall affect only magnitude calibration and meta_recommendation; it shall not deflate the `net_concern` numerical formula or its component scores because a candidate "deletes more".
- The lens is the generator-heavy Trias personality (weights generator 0.49 / control 0.30 / conservator 0.21) and is one of the three fixed personalities the Trias team dispatches.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## HOW — Acceptance (= tests)
AC-1
  Given  a set of candidates evaluated under Trias, one minimal/deletion-based and one additive, otherwise comparable
  When   the Essentialist lens is prepended to a core voice
  Then   the voice's chosen or most-favored candidate is the minimal/deletion-based option

AC-2
  Given  the Essentialist lens applied to the Generator voice
  When   the Generator produces its candidate spread
  Then   the spread still contains 3-5 candidates including a do_nothing/minimal option, with larger candidates present but ranked lower

## WHERE — Current implementation
- prompts/voices/essentialist_lens.md

## Why test_exempt

This file is a personality-lens overlay — plain text prepended to a core voice prompt at runtime by `personalities.py` for Trias mode. It contains no executable Python logic; conformance is validated through Trias deliberation integration runs. Deterministic guards (frontmatter + bias-keyword signature) live in scripts/test_lens_bias.py.
