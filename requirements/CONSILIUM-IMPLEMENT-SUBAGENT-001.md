---
milestone: v1.1
id: CONSILIUM-IMPLEMENT-SUBAGENT-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-IMPLEMENT-PIPELINE-001, CONSILIUM-SUBAGENT-001]
test_exempt: "agent spec document — behavioral contract validated by Step 7 auto-dispatch integration and implement-subagent smoke tests"
---

# consilium-implement-subagent

> WHY: Post-deliberation implementation vehicle that translates a GO Consilium report into written code + tests. Keeps implementation work out of the orchestrator context, enforces disjoint-path ownership between Coder and Test Writer, and gates output with Red→Green test verification.

## WHAT — Contract (normative)
- The system shall provide a `consilium-implement-subagent` agent that, given a GO Consilium deliberation report, executes the Coder → (Test Writer ∥ Reviewer) pipeline and returns a JSON file manifest — NOT a `.consilium/runs/` deliberation report.
- Pipeline sequence: (1) Coder writes implementation files; (2) Test Writer and Reviewer are dispatched in parallel on the written code; (3) Red→Green gate verifies tests are RED against a stub and GREEN against the real implementation.
- The subagent shall enforce disjoint-path ownership: Coder writes implementation files; Test Writer writes `test_*` files only; Reviewer writes nothing.
- If the Coder or Test Writer returns malformed or non-JSON output, the subagent shall retry that dispatch once; on second failure it shall abort and return `{"error": "subagent_json_invalid", "role": "<coder|test_writer>"}`. It shall never proceed on an empty or fabricated manifest.
- The subagent shall not re-run the deliberation; `chosen_approach` from the input report is the fixed spec.
- Output contract: strict JSON with `files_written`, `test_files_written`, `gate` (red_ok, green_ok, gate_passed), `gate_rejected`, `review`, `blocked`, `blocked_reason`.

## WHAT — Verify intent
- None — all questions resolved.

## HOW — Acceptance (= tests)
AC-1
  Given a GO report with non-empty chosen_approach and success_criterion
  When  the subagent runs
  Then  the final message parses as JSON matching the output contract, files_written exist on disk, test_files_written are test_* only, and no runs/<file>.json was created

AC-2
  Given a GO report where chosen_approach is do_nothing or skipped
  When  the subagent processes the input
  Then  it exits early (dry-run indicates skip) without writing any files

AC-3
  Given a Coder or Test Writer that returns malformed JSON
  When  the retry fires and also fails
  Then  the subagent returns the error JSON and does not proceed to the gate or manifest assembly

## WHERE — Current implementation
- agents/consilium-implement-subagent.md
