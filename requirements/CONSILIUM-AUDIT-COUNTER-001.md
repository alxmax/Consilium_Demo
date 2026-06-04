---
id: CONSILIUM-AUDIT-COUNTER-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# audit_counter

> Tracks the "every N sequential runs" silent parallel cross-check state machine.

## Input
- CLI flag `--increment`: bumps the sequential-run counter by 1
- CLI flag `--check`: reads state and decides whether a silent parallel audit is due
- CLI flag `--record-divergence 0|1`: logs the outcome of a completed audit (0 = match, 1 = divergent)
- CLI flag `--status`: prints a human-readable summary of audit state
- CLI flag `--mode`: informational label for the mode that triggered an increment (default: `sequential`)
- CLI flags `--sequential-chosen` / `--parallel-chosen`: chosen-IDs logged with each divergence record
- CLI flag `--state-path`: override path to state file (used by tests)
- Environment variable `CLAUDE_HEADLESS`: when set to `1`, `--check` returns `should_audit=false`
- `.consilium/audit_state.json`: persistent state file (read and written atomically)

## Description
Implements the "every N sequential runs" silent parallel cross-check mechanism described in SKILL.md section "Silent parallel audit". The orchestrator calls `--increment` after each sequential deliberation completes, `--check` before deciding whether to dispatch a parallel cross-run, and `--record-divergence` to log the outcome. When two or more divergences appear in the last five audits, the polling frequency automatically tightens from 1-in-20 to 1-in-5 runs; after a clean five-audit window at the hot frequency the interval relaxes back to 1-in-20. The state file is protected by a cross-platform advisory file lock (`msvcrt` on Windows, `fcntl` on POSIX) and written atomically via the shared utility to prevent concurrent-writer corruption. Idempotency is enforced via a `pending_audit_at` sentinel so repeated `--check` calls before `--record-divergence` cannot double-fire an audit.

## Output
- `--increment` stdout: JSON with `sequential_count` and `mode_recorded`
- `--check` stdout: JSON with `should_audit`, `sequential_count`, `frequency`, `last_audit_run`, `headless_skipped`, `already_pending`, `recent_divergences`
- `--record-divergence` stdout: JSON with `divergence_recorded`, `audit_count`, `frequency_before`, `frequency_after`, `frequency_changed`
- `--status` stdout: multi-line human-readable summary of counts, frequency, rolling window, and last 5 audit records
- `.consilium/audit_state.json`: updated on `--increment`, `--check` (when audit signalled), and `--record-divergence`
- exit code 0 on success; exit code 2 on invalid `--record-divergence` value

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- After exactly N sequential increments (where N equals the current frequency), `--check` returns `should_audit=true`; a subsequent `--check` before `--record-divergence` returns `should_audit=false` due to the `pending_audit_at` sentinel.
- After recording 2 divergences in a 5-audit rolling window while `frequency=20`, a subsequent `--record-divergence` call sets frequency to 5.
- After recording 5 consecutive non-divergent audits while `frequency=5`, the frequency reverts to 20.
- When `CLAUDE_HEADLESS=1` is set and an audit would otherwise be due, `--check` returns `should_audit=false` and `headless_skipped=true`.
- Concurrent calls to `--increment` do not corrupt the state file; each call increments the counter by exactly 1 due to the advisory file lock.
