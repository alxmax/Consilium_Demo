# Headless Invariants — Design Spec

**Date:** 2026-05-18
**Branch:** `feat/headless-invariants`
**Senate audit:** `runs/senate/2026-05-18_164154-mode-bugfix-performance.json` (v1, mode bugfix), mini-senate H2+H4 (7 senators in this session, verdict B+X 5/7 + 4/7)

---

## Goal

Optimizează deliberările Consilium când orchestratorul superior rulează `claude -p` headless (benchmark, CI, sub-agent dispatch). Elimină 4 prompt-trap-uri user-facing care în headless **consumă tokens fără a fi rezolvate** (modelul generează întrebări la care nimeni nu răspunde, apoi continuă oricum prin default).

**Success criterion:**
Cu `CLAUDE_HEADLESS=1` setat înainte de invocarea `claude -p`, o deliberare Consilium **NU** generează prompt-uri user-facing la Steps 0/2/5d/7. Toate cele 4 puncte de decizie folosesc default-uri documentate explicit. Output în `runs/*.json` rămâne valid (`validate_report.py` exit 0); raport conține metadata `headless: true` când aplicabil.

---

## Background

Benchmark-ul `C:\Users\ALEX\Desktop\Doc\benchmark-modes` rulează fiecare mod consilium via `claude -p`. Pe T00 warmup, Dialectic a consumat 46 turns + $2.00 + 13m26s — comparativ cu Sequential 28 turns + $0.77 + 4min pe același task. Diferența vine în parte din pași interactivi care n-au tratament headless explicit:

- **Step 0**: `priors.py` raportează `stale_pendings` → SKILL.md spune "întreabă user dacă vrea să le închidă". În headless: model generează întrebarea, nu primește răspuns, continuă.
- **Step 2**: `irreversibility_flag: true` → SKILL.md spune "confirmă cu user". În headless: la fel.
- **Step 5d**: confidence < 0.7 → SKILL.md spune "rulează retry_context.py înainte să întrebi user". În headless: re-rulează toate 3 voci, apoi log PEND_HEADLESS oricum. Retry-ul e wasted.
- **Step 7**: auto-pipeline → SKILL.md spune "interactiv: y/n prompt". În headless: --yes există ca flag, dar nu e enforced.

Skill-ul are deja un pattern aliniat: `CONSILIUM_FORCE_FULL=1` în `scope_gate.py` (escape hatch boolean) și `PEND_HEADLESS` outcome în `log_feedback.py` (deja documentat ca cale non-interactivă pentru Step 6).

---

## Architecture

Un helper Python (`is_headless()`) + 4 guard-uri documentate în SKILL.md la step-urile relevante. **Zero schimbări la voci, aggregator, confidence, scope_gate, sau senate flow.**

```
External orchestrator (claude -p invocation)
    │
    │ sets CLAUDE_HEADLESS=1
    ▼
Consilium workflow
    │
    ├── Step 0 priors: if is_headless() → log warning, skip user prompt
    ├── Step 1 clarity gate: existing PEND_HEADLESS pattern (unchanged)
    ├── Step 2 conservator veto: if is_headless() → log metadata, NU bloca
    ├── Step 3-4 voices: neschimbate
    ├── Step 5 aggregate: neschimbat
    ├── Step 5b confidence: neschimbat
    ├── Step 5c meta_critic: neschimbat
    ├── Step 5d retry: if is_headless() → skip integral
    ├── Step 6 report: PEND_HEADLESS existing (neschimbat)
    └── Step 7 auto-pipeline: if is_headless() → skip integral
```

---

## Components

### 1. `scripts/utils.py` — helper nou `is_headless()`

Adaugă o funcție pură care citește env var `CLAUDE_HEADLESS`. Pattern boolean `=='1'` aliniat cu `CONSILIUM_FORCE_FULL` (precedent în `scope_gate.py`).

```python
import os

def is_headless() -> bool:
    """True when CLAUDE_HEADLESS=1 — orchestrator runs via `claude -p`
    without an interactive user. Pattern aligned with CONSILIUM_FORCE_FULL=1
    from scope_gate.py.

    Skill steps that emit user-facing prompts MUST check this and choose
    a documented default path instead. See SKILL.md "Headless invariants".
    """
    return os.environ.get("CLAUDE_HEADLESS") == "1"
```

Locație: fișierul `scripts/utils.py` există deja (folosit pentru `force_utf8_streams`, `load_json_stdin`, `validate_keys`). Adăugare ~8 LOC + docstring.

### 2. `SKILL.md` — secțiune nouă "Headless invariants" + 4 step-edits + Dialectic H4 note

**Secțiune nouă (după "Memory tiers")**: definește contractul.

```markdown
## Headless invariants

Când `CLAUDE_HEADLESS=1` (set de orchestratorul extern care a invocat
`claude -p`), 4 puncte din workflow renunță la prompt-urile user-facing
și folosesc default-uri documentate. Pattern aliniat cu `CONSILIUM_FORCE_FULL`
din `scope_gate.py`. Helper: `from utils import is_headless`.

| Step | Default headless |
|---|---|
| 0 (stale_pendings) | log warning + continuă (NU întreba) |
| 2 (irreversibility_flag) | log în raport ca `headless_overridden: true` + continuă |
| 5d (retry on low conf) | skip integral; merge direct la Step 6 cu PEND_HEADLESS |
| 7 (auto-pipeline) | skip integral; orchestratorul extern decide pipeline |

`is_headless() == False` (env var absent) → comportament curent neschimbat.
Backward compat 100%.
```

**Step-edits** (4 locuri, ~5 linii fiecare):

- Step 0 bootstrap: adaugă paranteza `(headless: log warning, NU întreba)` la `stale_pendings` și `pend_pressure`.
- Step 2 Conservator veto-check: la `irreversibility_flag: true` adaugă bullet "Headless: loghează `headless_overridden: true` în report metadata, NU întreba consent. Orchestratorul extern care a setat env-ul a acceptat stake-ul."
- Step 5d retry on low confidence: adaugă "Headless: skip integral. Notă empirică: `retry_context.py` are zero labeled usage în `runs/` (vezi senate 2026-05-16_220025) — comportamentul aliniat cu deletion vote anterior."
- Step 7 auto-pipeline: adaugă "**Skip Step 7 dacă** ... sau `is_headless()`."

**Dialectic section H4 note** (~3 linii):

```markdown
**Effort guidance în headless.** Pass-1 sub-agents pot rula la `effort=medium`
(Pass-2 rămâne `high`). Decizia aparține orchestratorului extern; skill-ul
doar documentează posibilitatea — nu enforce-ază flag-ul CLI.
```

---

## Data flow

```
claude -p --env CLAUDE_HEADLESS=1
    │
    ▼
Orchestrator parses prompt → invokes /consilium
    │
    ▼
Step 0: priors.py runs normally → check stale_pendings
    │  if is_headless() → write warning to stderr, continue
    │  else → ask user (current behavior)
    ▼
Step 2: Conservator runs → if irreversibility_flag
    │  if is_headless() → set report.metadata.headless_overridden=true
    │  else → ask user "Confirmi că vrei să continui?"
    ▼
Steps 3/4: voices run → produce candidates/verdicts/scores
    │
    ▼
Step 5/5b/5c: aggregate + confidence + meta_critic (neschimbat)
    │
    ▼
Step 5d: if confidence < 0.7
    │  if is_headless() → skip retry, fall through to Step 6
    │  else → run retry_context.py, re-dispatch voices
    ▼
Step 6: build_report + log_feedback
    │  confidence < 0.7 path:
    │    if is_headless() → PEND_HEADLESS (existing behavior)
    │    else → ask user override (existing behavior)
    ▼
Step 7: if is_headless() → skip
    │  else → infer_pipeline + ask user y/n
```

---

## Error handling

- **`is_headless()` în context interactiv**: env var absent → `False` → comportament curent. Zero risc backward compat.
- **`is_headless()` accidental set în interactiv**: utilizatorul vede skip de la prompts, nu crash. Recoverable prin `unset CLAUDE_HEADLESS` și re-rulare.
- **Headless dar Step 2 ireversibilitate critică**: orchestratorul superior care a setat env var și-a asumat răspunderea. Metadata `headless_overridden: true` în raport pentru audit retroactiv.
- **Conflict semantic Step 5d skip**: `retry_context.py` are zero usage labeled în corpus (Socrate evidence). Skip-ul nu pierde nimic în practică.

---

## Testing

Smoke test manual (pattern existent în repo, no tests dir per CLAUDE.md):

```bash
# Test 1: helper returns True with env set
CLAUDE_HEADLESS=1 python -c "from scripts.utils import is_headless; assert is_headless()"

# Test 2: helper returns False without env
unset CLAUDE_HEADLESS
python -c "from scripts.utils import is_headless; assert not is_headless()"

# Test 3: helper returns False with env set to non-'1'
CLAUDE_HEADLESS=0 python -c "from scripts.utils import is_headless; assert not is_headless()"
```

Integration verification: rulează o deliberare scurtă cu `CLAUDE_HEADLESS=1` și verifică în `runs/<ts>_<label>.json` că:
- `metadata.headless: true` apare (dacă orchestratorul setează)
- niciun string `"Vrei să închid"` / `"Confirmi"` în transcript

---

## Scope boundaries

**Included:**
- `is_headless()` helper în `utils.py`
- 4 step-edits + secțiune nouă "Headless invariants" + Dialectic H4 note în SKILL.md

**Explicit excluded:**
- H2-C max_turns cap (suprapune `--max-turns` CLI; silent failure risk)
- H3 Senate headless (Senate nu invocabil de modele via `claude -p`)
- H4-Y `effort` în dispatch table (scope creep — orchestrator extern controlează)
- Schimbări la voci, aggregator, confidence, scope_gate, senate_synth
- Test suite formal (CLAUDE.md: no tests dir)
- Cod care impune env-ul (orchestratorul extern e responsabil să-l seteze)

---

## Files touched

| Fișier | Tip | LOC | Risc |
|---|---|---|---|
| `scripts/utils.py` | add `is_headless()` + docstring | +12 | trivial |
| `SKILL.md` | new section + 4 step-edits + Dialectic note | ~35 net | trivial (doc) |
| `docs/superpowers/specs/2026-05-18-headless-invariants-design.md` | this spec | +180 | doc |

**Total: ~47 LOC across 2 active files + spec. One commit on branch `feat/headless-invariants`** (per CLAUDE.md git workflow).

---

## Open questions (none blocking)

- **Q1.** Ar trebui ca `is_headless()` să accepte și `CLAUDE_HEADLESS=true` / `=yes`? **Decis NO** — strict `=='1'` aliniat cu `CONSILIUM_FORCE_FULL` precedent. Orchestratorul extern setează explicit.
- **Q2.** Notify în stderr când skipăm un prompt? **Decis YES pentru Step 0 + Step 2** (audit visibility), NO pentru Step 5d + 7 (curat).

---

## Senate consensus footnote

Mini-senate (7 senatori, această sesiune):
- **H2**: B=5 (Wittgenstein, Aurelius, Confucius, Dimon, Napoleon), A=2 (Socrate, Musk). Verdict **B** (skip Step 5d retry).
- **H4**: X=4 (Aurelius, Musk, Dimon, Napoleon), Y=2 (Wittgenstein, Dimon formal), Z=2 (Confucius, Socrate). Verdict **X** (doc-only în SKILL.md).
- Critical finding (Socrate): retry_context.py zero usage în corpus → H2-B = H2-A practic, implementare identică.

Senate-ul anterior (`runs/senate/2026-05-18_164154-mode-bugfix-performance.json`) cere ca pattern `DEPRECATED` să fie explicit pentru orice eliminare de mecanism — aplicat aici prin nota empirică inline despre Step 5d.
