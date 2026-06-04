# Open findings

> 123 open verify-intent item(s) across 41 requirement(s), aggregated from each requirement's `## WHAT — Verify intent` section by `reqmap.py findings`.
>
> These are open questions raised while reconstructing intent from code - NOT confirmed bugs. Resolve each by fixing the code or promoting the behavior into a Contract line. Run the AI triage pass (see SKILL.md) and drop a `_findings_triage.json` beside this file for a verified, prioritized view.

---

## CONSILIUM-AGGREGATOR-001 - aggregator  (3)

- When `conservative_override` is used and ALL candidates are vetoed with `auto_relax=False`, what is the expected output — `chosen: null` with no `retry_suggested`, or a different error shape?
- The `sequential` scheme operates on 'raw voice output dicts rather than numeric scores' — is the input schema for sequential mode formally defined anywhere, and what happens when the input contains both numeric scores and raw dicts?
- The veto cascade in `aggregate_sequential()` lists seven routing outcomes, but the acceptance tests only cover BLOCK (glossary_fail) and ESCALATE — is the behavior for REWORK, SHORT-CIRCUIT (scale_down), ADAPT_EXTENDED (scale_up), BLOCK (irreversibility), and plain AGGREGATE tested or specified anywhere?

## CONSILIUM-AUDIT-COUNTER-001 - audit_counter  (3)

- The tightening rule says 'two or more divergences in the last five audits' — does the rolling window of five count all audits or only those at the current frequency? What happens if frequency already tightened and only 3 audits have been recorded at the new frequency?
- The relaxation rule says 'five consecutive non-divergent audits while frequency=5' — does 'consecutive' mean no divergent entry anywhere in the window, or strictly in order with no gaps? Is the state reset if the system is reinstalled or the state file is deleted?
- When `--increment` is called with `--mode` set to a non-sequential mode (e.g. trias), is the counter still bumped, and is the frequency logic applied the same way? The description says 'every N sequential runs' but the flag accepts arbitrary mode labels.

## CONSILIUM-AUDIT-FEEDBACK-001 - audit_feedback  (3)

- The 'backfill' PEND row uses 'the same entry-building logic as `log_feedback.py`' — does that mean it also enforces the 0.70 confidence gate, or is that gate bypassed for backfill rows since no outcome is being claimed?
- When multiple missing runs are backfilled in one pass, are they appended in a defined order (e.g., by run timestamp, alphabetically by filename), or is the order undefined?
- What happens when `--check` is run and FEEDBACK.html does not exist at all — does it treat every run as missing and exit 1, or exit 0 because there are no rows to compare against?

## CONSILIUM-BUILD-REPORT-001 - build_report  (3)

- The description says skipped reports set `pipeline_executed: false`, but the acceptance test says `pipeline_executed` is 'absent or false' — which is the normative form? Does `validate_report.py` accept either, or only one?
- For the `why_not` derivation for non-chosen candidates, is the source of the text defined (Control issues only, Conservator risk note, or both combined), and what is emitted when a non-chosen candidate has no Control issues and no Conservator risk note?
- When both `--input` file and stdin carry data, which takes precedence? The description says 'stdin or `--input` file' without specifying conflict resolution.

## CONSILIUM-CHECK-DOC-DRIFT-001 - check_doc_drift  (3)

- The test-suite coverage check requires every `scripts/test_*.py` to appear in both `ci.yml` and the run-consilium driver — what is the exact string-matching rule used (filename stem, full path, partial match), and does the check distinguish between a file being listed but commented-out versus not present at all?
- The legacy MODE alias removal milestone check enforces 'dated removal comments accompany deprecated aliases' — what is the required date format and comment syntax? Is a future date accepted, or must the date have already passed?
- When a check fails with exit code 1 and multiple invariants are violated simultaneously, does the script print all violations before exiting, or stop at the first failure?

## CONSILIUM-CHECK-PUBLIC-LEAK-001 - check_public_leak  (3)

- The exact regex patterns are deliberately omitted from the doc — is there a secondary specification (comments in source, a separate config file) that a reviewer can consult to confirm correctness without reading the implementation?
- The guard 'skips binary and image file extensions' — is the skip list exhaustive and documented, or heuristic? What happens with a binary file that has a `.txt` extension (e.g., a compiled output accidentally committed as plain text)?
- When the script is run outside of a git repository (e.g., in a CI container where `git ls-files` fails), does it exit 0 (clean), exit 1 (as if a leak were found), or exit with a different code and message?

## CONSILIUM-CONFIDENCE-001 - confidence  (3)

- The blending formula is `0.7 * agreement + 0.3 * separation` — when there is only one candidate (no runner-up), what value is used for separation, and is this case explicitly tested?
- The `check_mode_floor` helper exempts structurally decisive Trias vote patterns (3-0, 2-1, 2-0) from the WEAK flag — is 2-0 truly 'structurally decisive', given that it represents a personality veto and only 2 of 3 personalities chose a candidate? Is this exemption intentional?
- The Steward dissent penalty is −0.10 and abstain penalty is −0.15 — are these penalties applied only for Steward, or for any dissenting/abstaining personality? The description specifies 'Steward-specific' but does not explain why Pioneer or Architect dissent carries no penalty.

## CONSILIUM-EFFICIENCY-001 - efficiency  (3)

- The metric is `total_tokens / ok_count` (lower is better) — but a Trias OK represents deeper deliberation than a Sequential OK; is there any normalization or weighting applied per mode, or is the raw metric always emitted as-is with only a caveat string?
- `tokens_per_dispatch` is 'normalized by number of voice calls' — how is the voice-call count determined for skipped runs (which have 0 voice calls), and are skipped runs included or excluded from this sub-metric?
- The `--since YYYY-MM-DD` filter 'filters out runs whose timestamp or filename stem sorts before the given date' — if the timestamp inside the run JSON and the filename stem disagree (e.g., a renamed file), which source takes precedence?

## CONSILIUM-FEEDBACK-001 - feedback  (3)

- The parser supports three HTML row layouts for backward compatibility — when a row matches multiple layouts (e.g., an 8-cell row that also satisfies the 7-cell count rule), which layout takes priority, and is there a defined precedence order?
- Rows with an unrecognized `outcome` field are 'silently skipped' — does this mean they are dropped from all stats (including total count), or counted in total but excluded from outcome breakdown? The distinction affects the success-rate calculation.
- The success rate excludes `PEND` entries — does it also exclude `PEND_HEADLESS`? The description only mentions excluding 'pending entries' but does not explicitly enumerate `PEND_HEADLESS`.

## CONSILIUM-IMPLEMENT-PIPELINE-001 - implement_pipeline  (3)

- The stub-insertion heuristic 'inserts `raise NotImplementedError` after each `def`/`async def`' — what happens when the function already contains a `pass` or `...` body, or when there are nested functions? Is the original file always fully restored on error?
- In plan mode the script 'emits a JSON plan for the orchestrating agent to consume' — is there a defined handoff schema between the plan JSON and the consilium-implement-subagent, and is that schema part of this requirement's contract?
- The exit code for `do_nothing`/`skipped` chosen approaches is 1, the same as gate failure — how does the caller distinguish between 'no pipeline needed' and 'gate failed'? Is that distinction intentional or an unresolved ambiguity?

## CONSILIUM-INFER-PIPELINE-001 - infer_pipeline  (3)

- The lookup table maps every `(magnitude, reversibility)` pair to a step list — is this table fully enumerated in the implementation, and what happens for pairs not in the table (e.g., `magnitude=trivial` with `reversibility=complete`)? Does the fallback to voice_scores scalar cover all such gaps?
- The description says the script 'never infers `irreversible` from the scalar because a floored net_concern is ambiguous' — is this constraint tested, and what step list is produced when the scalar is high but reversibility cannot be inferred?
- User rejections are persisted as `pipeline_rejected.json` events — is there any downstream consumer of these events (e.g., priors.py, efficiency.py), and if not, is the persistence intentional or a placeholder for future use?

## CONSILIUM-LENS-ARCHITECT-001 - architect lens  (3)

- AC-2 says the Conservator's `net_concern` 'may be adjusted upward via the quality-progress path, but not inflated solely because tests are absent' — what exactly is the 'quality-progress path', and is it defined in the Conservator voice contract or only in the lens prompt?
- The contract says the lens 'shall not inflate/deflate raw numerical scores directly' — but AC-1 says the voice 'ranks the well-structured candidate higher'; does 'ranking higher' imply a score difference, and if so, how is ranking without score change achieved?
- 'Trade-off judgments between architectural integrity and pragmatic speed are delegated to the multi-voice aggregator' — when Architect is applied to Conservator, does the lens ever affect which candidate Conservator prefers, or only the risk weighting?

## CONSILIUM-LENS-PIONEER-001 - pioneer lens  (3)

- The contract says Pioneer 'shall affect only magnitude calibration and meta_recommendation' when applied to Conservator, but AC-2 says '`net_concern` numerical value reflects the standard formula unchanged' — does 'magnitude calibration' mean the label only (low/medium/high/critical), or can Pioneer also shift the reversibility assessment?
- Does the Pioneer lens add any additional pressure to include or exclude the `unconventional_*` candidate, beyond what the Generator voice contract already requires?
- AC-1 says Pioneer favors 'the novel/ambitious option rather than the safe/incremental one' — is there a defined minimum gap in ambition between candidates for the lens to activate, or does it always prefer the most ambitious candidate regardless of how marginal the difference is?

## CONSILIUM-LENS-STEWARD-001 - steward lens  (3)

- The contract says Steward shall 'still produce the full required spread of candidates (3-5)' — but if all viable candidates are high blast-radius (e.g., a migration of a core system), what constitutes a 'minimal-blast-radius candidate' that Steward lists first when no genuinely minimal option exists?
- 'A new pattern is justified only when the existing pattern is INSUFFICIENT to meet the change requirements' — who decides insufficiency: the Generator voice, the Control voice, or the deliberation outcome? Is there a structured output field that records this judgment?
- When Steward is applied to Control or Conservator, does the 'order by smallest blast radius first' rule apply to their output ordering, or is the lens effect on non-Generator voices defined differently?

## CONSILIUM-LOG-FEEDBACK-001 - log_feedback  (3)

- The duplicate-detection fingerprint is keyed on `date|chosen|context|run_id` — if `run_id` is absent from the report (e.g., an older report format), does the fingerprint fall back to a 3-field key, and is that collision-safe for reports logged on the same day with the same chosen approach?
- The `--outcome OK` confidence gate requires `confidence >= 0.70` — is the `confidence` field read from the report's top-level key, or from the nested `confidence.confidence` dict form? What happens when the report carries both forms with different values?
- The row-upgrade path (PEND → OK) rewrites the existing row 'in place' — if two concurrent callers both attempt an upgrade on the same PEND row simultaneously, what prevents a race condition given that FEEDBACK.html is also protected by atomic writes?

## CONSILIUM-MARK-OUTCOME-001 - mark_outcome  (3)

- When matching by `--date` and `--chosen`, can multiple rows match (e.g., two runs on the same date with the same approach)? If so, are all matched rows updated, or only the first, and how is this communicated to the caller?
- The `[confirmed]` annotation is added to the note — if `mark_outcome` is called multiple times on the same row (e.g., BAD → OVR → OK), does the note accumulate multiple `[confirmed]` tokens, or is the existing annotation replaced?
- The `--outcome PEND_HEADLESS` path requires `--benchmark` as a guard — does the script verify that the row's current outcome is `PEND` before applying the transition, as implied by the 'non-PEND row' skip rule?

## CONSILIUM-MEMORY-001 - memory  (3)

- The short tier is 'a descriptive stub because its content is only accessible inside the active agent context window' — is the stub's output format fixed (always `entries: []` with a note string), or could future implementations populate it from a session file? If fixed, should the requirement say 'permanently a stub'?
- The `--query` flag applies a substring filter but the filter fields differ per tier — for medium it searches `success_criterion` + `chosen_approach`, for long it searches `context` + `chosen` + `note`; is case-insensitivity guaranteed for both tiers, and are the field names consistent with how those tiers store data?
- The `--n` flag limits entries 'per tier' — for `--tier all`, does `--n` apply independently to each tier (potentially returning up to 3N entries total), or is there a global cap?

## CONSILIUM-MODE-DIALECTIC-001 - dialectic mode  (3)

- AC-2 says the Skeptic is dispatched 'on the trivial-direct chosen' when Sequential short-circuits via `scale_down` — but the trivial-direct path produces a minimal report without full voice outputs; does the Skeptic receive a full deliberation bundle or only the scale_down stub, and is the Skeptic's challenge meaningful in that case?
- The cost is specified as '1.33× Sequential' — is this a contractual bound (implementation must not exceed it) or an informational estimate? What happens to cost accounting when the Skeptic sub-agent itself has a long context due to code-specific injection?
- When `--skeptic-can-override` is active and Skeptic produces `addressable: requires_redesign` — does override mean the `chosen` field in the report is replaced with a new candidate ID, or that the report is marked for re-deliberation? What is the exact output shape in the override case?

## CONSILIUM-MODE-SEQUENTIAL-001 - sequential mode  (3)

- The `confidence_floor: 0.70` is described as 'advisory' and 'NOT a hard gate' — but CONSILIUM-LOG-FEEDBACK-001 enforces a 0.70 confidence gate on `--outcome OK`; is this the same threshold operationally applied at two different points, and does below-floor confidence in Sequential prevent logging OK without `--force-override`?
- The veto-budget for `meta_recommendation` is '5 activations per month; on exhaustion the gate becomes a soft warning only' — where is this budget tracked, and what resets it at month boundaries? This appears unimplemented; is it aspirational or enforced?
- The auto-parallel cross-check triggered on `magnitude: critical AND reversibility: irreversible` — is this distinct from the 1-in-20 silent parallel audit, and if so, is there a separate state machine or counter for it?

## CONSILIUM-MODE-TRIAS-001 - trias mode  (3)

- The B2 deadlock cascade fires on '1-1-1 or 0-0-0' — what does 0-0-0 mean in the context of three personalities each choosing a candidate, and is 0-0-0 achievable only when a personality abstains?
- Lazy routing downgrades to Dialectic for `high` magnitude — does the lazy-routed Dialectic run carry the `trias_lazy_routed: true` field all the way into the final persisted report, and does it affect how priors or efficiency metrics classify the run?
- Context is 'truncated to ≈15 000 tokens before dispatch' — what is the exact truncation strategy (last N tokens, first N tokens, or smart summarization), and is the 15 000 token budget a hard limit or a target?

## CONSILIUM-PERSONALITIES-001 - personalities  (3)

- The weights for Pioneer are `generator 0.49` but the full weight tuple is not shown — what are the `control` and `conservator` weights for Pioneer, and do the three personalities' weight vectors differ in a way meaningful enough to document here?
- `get_by_name()` returns 'a deep copy to prevent mutation' — is the deep-copy behavior tested, or only stated? If the registry is a module-level dict of dicts, a shallow copy could still allow nested mutation.
- The legacy positional integer argument is rejected with exit code 2 — what was the old positional-N API, and is there a migration path documented anywhere for callers that still use the old form?

## CONSILIUM-PRIORS-001 - priors  (3)

- `conservator_veto_rate` ignores sequential BLOCK/REWORK by design (only `conservative_override` counts as a veto) — should this constraint be stated explicitly in the requirement to prevent future 'fixes' that accidentally count sequential blocking outcomes?
- `weighted_bad_rate` is listed in the signals but not defined — what is the weighting scheme (recency, outcome type, confirmed vs. unconfirmed rows), and how does it differ from plain `bad_rate`?
- `STALE_PEND_DAYS` is referenced but not pinned in the requirement — what is the value, is it hardcoded or configurable, and does the requirement intend to pin it?

## CONSILIUM-PROBE-CHANGE-001 - probe_change  (3)

- The default mode 'diffs staged + unstaged changes against HEAD' — does this include untracked files, or only tracked modified files? The behavior for untracked files is relevant when a developer adds a new file without staging it.
- `--ref` and `--range` are 'mutually exclusive' — what is the exact error output and exit code when both are supplied simultaneously?
- The `--churn N` per-file commit frequency is computed 'over the last N days via `git log --since`' — is the commit count for each file the number of commits touching that file specifically, or total repo commits in the window?

## CONSILIUM-RENDER-FEEDBACK-HTML-001 - render_feedback_html  (3)

- The `(calc)` token estimate uses 'the median tokens-per-candidate of peer runs' — how are 'peer runs' defined (same mode, same date range, all runs)? An undefined peer set makes the estimate non-reproducible.
- The VETOED badge is sourced from the aggregate step's `vetoed` list — what if the run was produced by the `sequential` scheme, which does not produce a `vetoed` list in the same format? Is there a fallback, and is the Conservator drill-down panel suppressed or shown without vetoed badges?
- The HTML is described as 'self-contained' with no external asset references — is this verified by the acceptance test, or only stated? A test that checks for the absence of `<link>` and `<script src>` tags would confirm it.

## CONSILIUM-RETRY-CONTEXT-001 - retry_context  (3)

- The script is 'deliberately one-shot and does not execute the deliberation itself, capping the retry loop at one attempt' — but the requirement says the orchestrating agent 'dispatches one additional Generator/Control/Conservator pass'; is the cap enforced by the script itself, by the orchestrator, or only by convention?
- The top-2 candidates are selected by 'a composite utility score (mean of generator pass, control validity, and inverted conservator risk)' — what happens when fewer than 2 candidates pass Control validation (valid=true)? The acceptance test covers 'only one valid candidate', but what about zero valid candidates?
- The regex patterns extract 'file paths, symbol names, dotted attribute paths, and backtick-quoted tokens' — is there a documented limit on how many patterns are extracted per candidate before the 4-item cap is applied?

## CONSILIUM-RUN-EVALS-001 - run_evals  (3)

- The description says stdout matching uses 'either a JSON subset-match or a plain-text substring match' — what determines which mode is used for a given scenario? Is it a field in `scenarios.json` (e.g., `expect_stdout_type`), and is the subset-match semantics defined (exact key equality, recursive inclusion, or type-only check)?
- The pre-flight linter checks for `pipeline_executed` in `validate_report` fixtures — does it also check that non-validate_report scenarios that produce a full report include `pipeline_executed`, or is the lint scoped only to `validate_report` fixtures?
- When `--filter` matches zero scenarios, the script exits 2 with 'no scenarios matched' — is this the same exit code as a corpus load error? Could the caller distinguish 'filter found nothing' from 'scenarios.json is malformed'?

## CONSILIUM-SCOPE-GATE-001 - scope_gate  (3)

- The `mode_ceiling` output field maps magnitude to a maximum deliberation mode — is the full mapping table (low→?, medium→?, high→?, critical→trias) specified anywhere, or only the critical→trias case documented in the acceptance tests?
- When `--signals-stdin` is used, the `paths` field is accepted — but the blocklist check requires path matching; is the `paths` field compared against the blocklist the same way as git-diff paths, and what format are paths expected in (relative to repo root, absolute, etc.)?
- The gate 'fails open' on probe failures — but `CONSILIUM_FORCE_FULL=1` also returns `should_skip=false`; do both paths produce identical JSON shapes, or does the forced-full path produce a different reason field?

## CONSILIUM-STABILITY-CHECK-001 - stability_check  (3)

- The 0.80 veto boundary is hard-coded as the reference for the 'uncertain band' analysis — is this value the same as the `veto_threshold` in `aggregator.py`, and if aggregator's threshold is changed, does stability_check need to be updated in sync?
- The Bug #1 verdict threshold of 0.10 mean pstdev is a fixed constant — is this threshold empirically derived or arbitrary? Should the requirement document who can change it and under what circumstances?
- In compare mode, what constitutes a 'same input' constraint when comparing two runs? The description says 'two runs on the same input' but there is no enforcement or input-hash comparison — is this purely a human convention?

## CONSILIUM-STRIP-CONTEXT-001 - strip_context  (3)

- In `--for conservator` mode, 'valid Control verdicts' are intersected with Generator candidates — what happens when a Generator candidate has no matching Control verdict (e.g., Control was partial)? Is the candidate included (with no verdict data), excluded, or is this treated as an error?
- The `--truncate-text` mode approximates tokens as '4 chars/token' — is this approximation documented as intentionally coarse, and is there a risk of over- or under-truncation for non-Latin scripts (e.g., Romanian diacritics or code with multi-byte chars)?
- The truncation marker is 'appended when the text is cut' — what is the exact marker string, and is it defined in a shared constant or duplicated across scripts that consume the truncated output?

## CONSILIUM-TRACE-GRAPH-001 - trace_graph  (3)

- A 'prior-deliberation passthrough run produces a two-node graph `PRIOR -> REP`' — but a passthrough run may still have metadata (confidence, chosen approach) worth showing; is the two-node minimal graph intentional, or should it show the passthrough's source run reference?
- For a sequential run with a Skeptic, the graph shows 'an advisory edge from AGG to SKP and from SKP to REP' — but when the Skeptic overrides the chosen candidate (`--skeptic-can-override`), should the edge semantics change (e.g., a different edge label or a direct replacement edge)?
- The output is described as 'valid Mermaid' — is there a validation step in the acceptance test, or is correctness only confirmed by visual inspection at mermaid.live?

## CONSILIUM-USAGE-001 - usage  (3)

- For Trias or parallel mode runs, latency reflects 'the maximum voice latency rather than the sum' — but Trias runs have 3 sub-agents each running 3 voices; is 'voice latency' the latency per sub-agent's full Sequential run, or per individual voice call within each sub-agent?
- The latency spike detection flags 'any voice whose latency exceeds 2x the median of its peers' — are 'peers' defined as all voices in the same run, or the same named voice across all runs in the dataset?
- `--last N` restricts to 'the most-recent N run files' — is 'most-recent' determined by file modification time, filename sort order (which encodes timestamps), or the `telemetry.timestamp` field inside the JSON?

## CONSILIUM-UTILS-001 - utils  (3)

- `atomic_write_text` uses 'a sibling `.tmp` file' — what happens when the parent directory is read-only or the `.tmp` file already exists from a previous crashed write? Is there a defined cleanup behavior or stale-lock detection?
- `DATA_DIR`, `RUNS_DIR`, and `FEEDBACK_PATH` resolve 'relative to the repo root' — how is the repo root determined (e.g., by walking up from `__file__`, from `git rev-parse`, or from CWD)? If a script is invoked from outside the repo, does this break silently or raise a clear error?
- `issue_penalty` returns `0.15` for 'medium or missing severity' — treating missing severity the same as medium is a silent normalization; is this intentional, and should callers be warned when severity is absent rather than silently defaulting?

## CONSILIUM-VALIDATE-REPORT-001 - validate_report  (3)

- The requirement says `chosen_approach` may be 'null (conservative-override veto case)' — but are there other valid null cases (e.g., a BLOCK outcome from the glossary_fail path), and does the validator distinguish between intentional nulls and missing fields?
- The check for `deliberation_log` requires 'an aggregate step whose `result` is a dict (not a string narrative)' — what other steps must be present in `deliberation_log` for a non-skipped report, and are missing steps (e.g., a report missing the `conservator` step) caught by the validator?
- Telemetry 'counts (token/latency) are non-negative ints where present' — does the validator reject float values (e.g., `1500.0` instead of `1500`), and is the 'where present' qualifier precisely defined (which telemetry sub-fields are required vs. optional)?

## CONSILIUM-VERSION-001 - version  (3)

- `consilium_ref()` returns `''` when the working tree has uncommitted tracked changes — does 'uncommitted tracked changes' include staged-but-not-committed changes, or only unstaged modifications? The distinction matters for CI environments that stage files during build.
- `prompts_changed_since` returns 0 silently for unresolvable refs — but a caller that passes a stale ref (e.g., a deleted branch) would receive 0 and incorrectly conclude no prompts changed; is silent 0 the right behavior, or should there be an out-of-band signal indicating resolution failure?
- The `--drift REF` flag diffs only `prompts/` and `modes/` — but `scripts/aggregator.py` and `scripts/confidence.py` also affect deliberation behavior; is restricting drift detection to prompts and modes intentional, or an omission?

## CONSILIUM-VOCABULARY-MAP-001 - vocabulary_map  (3)

- `translate` returns `str(value)` for unknown category or value without raising — callers that silently receive the raw value string instead of a human-readable label may produce confusing output; is this the intended degradation behavior, or should unknown values at least be logged?
- The output language is Romanian (e.g., `usor de anulat`) — is Romanian the only supported output language, or is there an internationalisation hook? If Romanian-only, is this a design decision that should be stated explicitly?
- `compute_tokens_budget` with `meta='scale_up'` returns '+50% capped at 4000' — what is the base value before the 50% uplift, and for which `(magnitude, reversibility)` pairs does the cap actually bind?

## CONSILIUM-VOICE-CONSERVATOR-001 - conservator voice  (3)

- The mitigation cap is 'discipline-based with no automated schema enforcement' and 'audited through notes' — who performs this audit, when, and what action is taken if a Conservator output violates the cap? Should the requirement acknowledge this limitation explicitly?
- The three irreversibility fields can 'coexist on the same candidate' — the requirement acknowledges this as 'a persistent source of confusion' but provides no resolution rule; should the requirement define which field takes precedence when they conflict?
- When `meta_recommendation: scale_down` overrides the token budget to 300 'regardless of magnitude×reversibility', can Conservator still emit `magnitude: critical`? If yes, the Trias lazy-routing logic that triggers on `critical` magnitude may be at odds with the scale_down intent.

## CONSILIUM-VOICE-CONTROL-001 - control voice  (3)

- `confidence_in_verdict: low` is 'advisory only — the aggregator does not automatically discount verdicts marked `low`' — this means a speculative `valid: true / low` verdict influences the final recommendation as strongly as a high-confidence one; is this intentional or a known limitation to eventually fix?
- AC-2 says Control still emits verdicts even when `glossary_fail: true` — but the aggregator BLOCKs on glossary_fail before Generator runs; does Control run after Generator in Sequential mode, meaning a glossary_fail not caught before Generator ran will still have Control emit verdicts on Generator's candidates?
- The 3-entry cap on `hidden_assumptions` 'trusts the voice to surface the most consequential assumptions' — is there any retrospective signal that lets the development team detect cases where the cap caused a critical assumption to be dropped?

## CONSILIUM-VOICE-GENERATOR-001 - generator voice  (3)

- The `adversarial_<short_id>` candidate is included when 'the change touches shared/core code or a function with more than 3 external callers' — how does the Generator voice determine the external caller count without file access? Is this a heuristic self-assessment, and if so, is the 3-caller threshold reliably applied?
- The voice-score handicap of 0.5 applied to `adversarial_*` and `do_nothing` is applied 'downstream by `build_report.py`' — but could a Generator output that explicitly sets a score for these candidates override the downstream handicap?
- The `unconventional_*` omission rule allows omission when 'the change is mechanically trivial' — is 'mechanically trivial' defined anywhere, and does it overlap with Conservator's `meta_recommendation: scale_down`?

## CONSILIUM-VOICE-SKEPTIC-001 - skeptic voice  (3)

- 'Validation failure results in silent discard' — is there any telemetry or log entry written when a Skeptic output is silently discarded, so that the development team can detect prompt regressions that cause systematic silent discard?
- `meta_scope_mismatch` requires `addressable: unaddressable` — but the description says the failure mode is 'resolvable in under 10 seconds by a human'; does `unaddressable` make sense when the human can resolve it? Should this failure mode use a different `addressable` value?
- When `can_object: true` but `concrete_concerns` has only 1 entry and `quoted_scenario` is null, the output is 'discarded silently' — does the orchestrator log the discard reason, or is the discard completely invisible to the pipeline report?

## CONSILIUM-VOTE-DEGENERACY-001 - vote_degeneracy  (3)

- The scan uses 'a text-based scan, not `json.loads`' to extract `vote_pattern` — what is the exact regex pattern used, and could it produce false positives from runs that contain the string `vote_pattern` in a note or rationale field but are not Trias runs?
- The 2-0 veto pattern is tracked separately as `veto_rate` — but in CONSILIUM-MODE-TRIAS-001, 2-0 is listed as a confidence value (0.70); is a 2-0 vote pattern always a veto, or can it represent two personalities choosing one candidate and the third abstaining?
- The threshold of 0.85 and minimum N of 20 are defaults but configurable — is there any guidance on what values are appropriate for different corpus sizes, or is the choice left entirely to the caller?

## SKILL-RUN-CONSILIUM-001 - run-consilium driver  (3)

- `smoke` mode 'exits non-zero only when failures exceed a documented baseline' — where is the baseline documented, and what is it? If some test suites are known-failing, are they excluded from the failure count or counted against the baseline?
- In `shot` mode, the script 'checks for Chrome/Edge at known Windows paths' — what are those paths, and what happens on non-Windows platforms (Linux, macOS CI)? Is the `shot` command expected to work cross-platform, and if not, should it exit with a clear error rather than silently failing?
- `pipeline` mode prints 'aggregator JSON, confidence JSON, and validate_report result' — but the description also mentions `build_report` as a pipeline stage; does `pipeline` mode run all four stages (aggregator → confidence → build_report → validate_report) or only three?

