# FEEDBACK.md → FEEDBACK.html — Design Spec

**Date:** 2026-05-12
**Status:** Draft (awaiting user review before implementation plan)
**Scope:** Migrate the manual feedback journal from a Markdown table to an HTML file with dark theme and per-entry drill-down to the corresponding `runs/*.json` voice outputs.

---

## Goal

Replace `skills/consilium/FEEDBACK.md` (plain MD pipe-table) with `skills/consilium/FEEDBACK.html` (dark-themed sortable table with row-level drill-down to Generator / Control / Conservator outputs). User opens the file with a double-click and gets:

- A scannable table of all past deliberations (date, context, chosen, outcome, note) — same columns as today, colored outcome.
- A click-to-expand drill-down per row showing the actual candidates, validation verdicts, and risk scores from the corresponding `runs/<file>.json` — no more cross-referencing two files manually.

**Success criterion:** After migration, opening `FEEDBACK.html` in a browser shows all 13+ existing entries with correct dates/outcomes; clicking a row with an associated `runs/*.json` expands a 3-column panel (Generator candidates, Control verdicts with valid/invalid badges + tests, Conservator risk scores with factor breakdown). `priors.py`, `feedback.py`, and `log_feedback.py` continue to function (read/append) against the new HTML format. Old `FEEDBACK.md` is preserved as `.md.bak` for rollback.

**Verification:**
1. Open `FEEDBACK.html` in Chrome/Edge — all rows present, dark theme renders, OK/BAD/OVR/PEND colored correctly.
2. Click row 4 (`disable_when_unreachable`) — drill-down expands with 3 voice columns populated from `runs/2026-05-11_2030_live-rerun-resilience.json`.
3. Run `python scripts/priors.py` — returns JSON with same `override_rate`/`bad_rate`/keywords as before migration.
4. Run `cat runs/<latest>.json | python scripts/log_feedback.py --outcome OK` — new row appears at bottom of `FEEDBACK.html` with correct drill-down embedded.

---

## Motivation

The MD pipe-table works but is painful at 13+ entries and growing:
- Visual scan is hard — long `note` fields wrap awkwardly in raw MD viewers.
- No color coding — `OK`/`BAD`/`OVR`/`PEND` look identical at a glance.
- Drilling into voice details requires opening the corresponding `runs/*.json` separately and reading JSON by hand.
- No grouping/filtering.

HTML solves all four with ~50 lines of CSS and ~10 lines of vanilla JS, no dependencies.

---

## Format

Approved preview at `docs/feedback-preview.html` (committed to the skill for reference). Single self-contained HTML file:

- Dark theme (`#16161a` bg, `#d6d6d6` fg, accents per outcome).
- `<table>` with thead/tbody/`<tr class="entry">` pattern.
- Each entry row is followed by a sibling `<tr class="drill">` (hidden by default; toggled by inline `onclick="toggleDrill(this)"`).
- Drill-down content: `<div class="drill-grid">` with 3 `<div class="voice">` panels.
  - **Generator panel**: candidates list (id, summary, sketch) with `CHOSEN` badge on the picked one.
  - **Control panel**: per-candidate `valid`/`invalid` badge + issues (✕ prefix) + tests (✓ prefix).
  - **Conservator panel**: per-candidate `risk_score` (color-coded low/mid/high), factor grid (diff/scope/regr/rev), `VETOED` badge if `risk_score >= 0.7`.
- Inline `<style>` and `<script>` blocks (no external deps).

Mockup is in `docs/feedback-preview.html` — implementation must match it visually.

---

## Implementation Components

### 1. `scripts/render_feedback_html.py` (new)
Pure render function. Reads `runs/*.json` files + an in-memory list of entries; emits the full `FEEDBACK.html`.

**Interface:**
```python
def render(entries: list[Entry], runs_dir: Path) -> str:
    """Return full HTML string. entries is the parsed list; runs_dir resolves drill-down."""
```

**Entry → run mapping:**
- Entries store `run_path` field pointing to the source JSON (or `None` for legacy pre-runs/ entries).
- Mapping rule: when an entry is logged via `log_feedback.py`, the script knows the run path (it's what's piped into stdin via the file argument or `--run-path` flag); embed it in the HTML row as `data-run="runs/<file>.json"`.
- For migrated legacy entries (lines from old `FEEDBACK.md`), `run_path` is `None` → drill-down shows the stub "no detailed run data — older entry pre-runs/".

**Decision: static pre-render, not lazy fetch.**
- Pro: opens via `file://` (double-click) — no HTTP server required.
- Pro: `FEEDBACK.html` is self-contained; portable.
- Con: editing a run JSON manually doesn't auto-update HTML — requires re-render.
- Acceptable: run JSONs are rarely hand-edited; `log_feedback.py` re-renders on every append.

### 2. `scripts/log_feedback.py` (modified)
Switch from "append line to MD" to "append entry to HTML".

**New behavior:**
1. Read existing `FEEDBACK.html` (or initialize empty list if missing).
2. Parse current entries from `<tr class="entry">` rows (regex on `<td>` cells, same fields).
3. Build new entry dict from stdin report (same fields as today + `run_path`).
4. Call `render_feedback_html.render(entries + [new_entry], runs_dir)`.
5. Write back to `FEEDBACK.html`.

**Inputs unchanged:** stdin JSON report, `--outcome`, `--override-target`, `--user-note`, `--dry-run`, `--feedback` (now defaults to `./FEEDBACK.html`).

**New input:** `--run-path PATH` — explicit pointer to the source `runs/*.json`. If omitted, falls back to drill-down stub.

### 3. `scripts/migrate_feedback_md_to_html.py` (new, one-shot)
Reads existing `FEEDBACK.md`, parses lines matching `- YYYY-MM-DD | ctx | chosen | outcome | note`, builds entries list, attempts to fuzzy-match each entry to a `runs/*.json` file (by date + chosen approach + closest timestamp), calls `render_feedback_html.render(...)`, writes `FEEDBACK.html`. Renames old file to `FEEDBACK.md.bak`.

**Fuzzy match heuristic:**
1. Same date.
2. `chosen_approach` in run JSON matches MD `chosen` column.
3. If multiple matches, pick the one whose `success_criterion` shares the most tokens with the MD `context` column.
4. If zero matches, `run_path=None` (legacy stub).

User runs this manually once.

### 4. `scripts/priors.py` (modified parser)
Replace MD line regex with HTML row regex. Parse `<tr class="entry">...</tr>` blocks; extract `<td>` cells in order. The schema is identical (date | context | chosen | outcome | note). ~10-15 lines changed.

Override/bad/conservator-veto rates and keyword extraction logic remain identical.

### 5. `scripts/feedback.py` (modified parser, if exists)
Same parser swap as `priors.py`. Verify whether script exists / is in use; if not used, skip.

### 6. `SKILL.md` (text-only updates)
Replace references from `FEEDBACK.md` to `FEEDBACK.html` in:
- "Feedback loop (artefacte)" section.
- Step 0 (`priors.py` reads from `FEEDBACK.html`).
- Step 6 (auto-log).
- "Skill maintenance" audit section.

No workflow logic changes.

---

## Data Flow After Migration

```
deliberation finishes (Step 6)
    │
    ▼
runs/<file>.json written (unchanged)
    │
    ▼
log_feedback.py --run-path runs/<file>.json
    │
    ├─ parse existing FEEDBACK.html entries
    ├─ append new entry with run_path
    └─ render_feedback_html.render() → write FEEDBACK.html
    │
    ▼
next session: priors.py reads FEEDBACK.html rows → soft priors
```

---

## File Locations Summary

| Path | State after migration |
|---|---|
| `skills/consilium/FEEDBACK.html` | new, live, gitignored |
| `skills/consilium/FEEDBACK.md.bak` | one-time backup of legacy MD |
| `skills/consilium/FEEDBACK.md` | deleted (lives only as `.bak`) |
| `skills/consilium/runs/*.json` | unchanged |
| `skills/consilium/docs/feedback-preview.html` | committed reference mockup |
| `skills/consilium/scripts/render_feedback_html.py` | new |
| `skills/consilium/scripts/migrate_feedback_md_to_html.py` | new (one-shot) |
| `skills/consilium/scripts/log_feedback.py` | modified |
| `skills/consilium/scripts/priors.py` | modified (parser only) |
| `skills/consilium/scripts/feedback.py` | modified (parser only, if used) |
| `skills/consilium/SKILL.md` | text references updated |

`.gitignore`: `FEEDBACK.html` and `*.md.bak` should be gitignored (same as `FEEDBACK.md` today — personal/local journal).

---

## Out of Scope

- **Search/filter UI** — no input boxes, no client-side filtering. Browser Ctrl+F suffices.
- **Sortable columns** — outcome column ordering is chronological; sort can come later if needed.
- **Cross-skill HTML** — `runs/*.json` keep JSON; rendering them individually as HTML is a separate, optional task.
- **Telemetry/charts** — `scripts/usage.py` continues to emit text/JSON; not visualized here.
- **`runs/README.md` schema doc** — unchanged (still describes JSON schema, not HTML).

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Fuzzy match in migration script picks wrong run for an entry | Migration script prints `match_log` (entry → run mapping). User can inspect and re-run with manual overrides if needed. |
| `priors.py` parser breaks on edge cases (entry with embedded `</td>` in note) | Note text passed through `html.escape()` at render time; parser uses lenient regex with `re.DOTALL`. |
| User accidentally double-runs migration → overwrites HTML | Migration script aborts if `FEEDBACK.html` already exists unless `--force` is passed. |
| HTML render is slow at 100+ entries | Negligible — pure string concatenation, no DOM. Test at 100 entries during plan. |
| File:// drill-down works but no copy-paste of run path | Acceptable — drill-down embeds the data directly, not a link to the JSON. |

---

## Open Questions (all closed by user during brainstorming)

- ~~Dark vs light theme?~~ → Dark (preview approved).
- ~~3-column drill-down or tabbed?~~ → 3-column (preview approved).
- ~~Static pre-render or lazy fetch from runs/?~~ → Static (decided in this spec — simpler, no HTTP requirement).
- ~~Keep old `FEEDBACK.md`?~~ → Backup as `.md.bak`, delete original after migration.
