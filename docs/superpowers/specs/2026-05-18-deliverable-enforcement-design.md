# Deliverable Contract Enforcement — Design Spec

> ⚠ **POST-MORTEM (added 2026-05-18 22:00) — THIS SPEC DESCRIBES A FAILED APPROACH.**
>
> The Step 6.5 textual rule was implemented as designed below. Empirical
> T1 re-run on `code/00_warmup` showed `solution.py` STILL not on disk;
> same failure mode as the prior `CONSILIUM_SUFFIX` attempt. Hidden
> assumption #3 (see Section 0 below) — *"textual rule sufficient to
> force tool-call behavior"* — was **INVALIDATED**.
>
> Senate audit on the failure (`runs/senate/2026-05-18_203925-deliverable-enforcement-r2.json`,
> MODIFY 7-0) recommended moving authority for deliverable file presence
> to the harness layer. Implemented in:
>
> **`benchmark-modes/scripts/extract_deliverables.py`** (alxmax/Benchmark
> commit `81fd6a4`, merged via PR #4 on 2026-05-18). Harness post-processes
> `claude_raw.json`, extracts fenced code blocks matching declared
> filenames, writes them to disk. Idempotent. Stdlib-only.
>
> Consilium-side outcome: `runs/2026-05-18_2012_skill-step-6-5-deliverable-enforcement.json`
> marked `BAD [confirmed]` via `mark_outcome.py` (2× weight in priors).
> No production `SKILL.md` change shipped — Step 6.5 was reverted.
>
> This document is preserved as the historical record of the in-skill
> attempt. **Do not implement.** Use the harness-level solution instead.

---

**Date:** 2026-05-18
**Scope:** SKILL.md (Step 6.5 nou) + `../benchmark-modes/run_task.py` (cleanup `CONSILIUM_SUFFIX`)
**Trigger:** orice consilium run unde prompt-ul declară explicit fișiere de livrat (header dedicat sau frază inline)
**Sursa problemei:** `workspace/consilium_sequential/code/00_warmup/` din benchmark — modelul a produs blueprint-ul `solution.py` ca fenced code block în răspuns, dar n-a apelat niciodată `Write`. `verify.py:88-95` a returnat `solution.py not found in workspace root` → score `0/60` în loc de `60/60`.

---

## Obiectiv

Closing line-ul deliberării (`chosen: <id> | conf: <X> | runs/<file>.json`) nu trebuie să poată fi emis până când fișierele declarate în contractul task-ului nu există fizic pe disc. Cod într-un fenced block din răspunsul în chat **nu** este un livrabil acceptat.

## Non-Goals

- Nu modificăm niciunul din prompt-urile de benchmark (`prompts/code/*.md`, `prompts/reasoning/*.md`). Cerință explicită a userului.
- Nu introducem dependențe externe sau scripturi noi (stdlib-only per CLAUDE.md).
- Nu schimbăm semantica Step 7 (auto-pipeline) — rămâne opt-in, post-report.
- Nu generalizăm enforcement-ul peste consilium-ul pe diff/refactor/PR review unde promptul **nu** declară fișiere — regula trebuie să fie no-op acolo.

---

## 1. SKILL.md — Step 6.5 nou (inserat între Step 6 și Step 7)

### Conținut exact al secțiunii

```markdown
### 6.5. Deliverable contract enforcement (auto)

Dacă input-ul task-ului declară explicit fișiere de livrat — fie via secțiune
dedicată (ex: `**Required output files**`, `**Deliverables**`), fie via frază
inline ("save your response to `<file>`", "deliver `<file>`", "write to
`<name>`") — TREBUIE să scrii fiecare fișier pe disc **înainte** de a emite
linia finală.

**Acțiunea:**
1. Identifică fiecare filename declarat (backticked, relativ la `cwd`).
2. Pentru fiecare, apelează `Write` cu conținutul implementării
   `chosen_approach` (codul/textul produs în cursul deliberării — pentru
   cod, implementarea concretă a `chosen` candidate-ului; pentru reasoning,
   răspunsul concret cerut, ex. `ANSWER: <letter>` + motivație).
3. Verifică prezența cu `Read <file>` sau `ls`. Dacă lipsește, retry `Write`
   o singură dată; dacă tot lipsește, adaugă `deliverable_write_failed:
   <file>` în `notes` al raportului final și emite linia.

**Gate (obligatoriu):**
- Codul într-un fenced block din răspuns NU este un livrabil acceptat.
  Doar `Write` pe disc satisface contractul.
- Linia finală `chosen: <id> | conf: <X> | runs/<file>.json` se emite
  **doar după** ce toate fișierele declarate există pe disc (sau au fost
  raportate ca `deliverable_write_failed`).

**Nu se aplică dacă:**
- Promptul nu declară niciun deliverable (consilium pe diff / refactor /
  PR review) — Step 6.5 trece transparent.
- `chosen_approach ∈ {"do_nothing", "skipped"}` — nimic de scris.
```

### Justificare pattern-by-pattern

| Element | Motiv |
|---|---|
| Trigger comportamental, nu regex | Cele 4 prompt-uri benchmark folosesc 3 formulări diferite: `**Required output files**`, `**Required output file:**`, inline phrasing `save your response to ...`. Un regex care le acoperă pe toate e fragil; unul lax e fals pozitiv pe context (ex: orice mențiune backticked de filename ca referință documentară). Modelul deja recunoaște contracte de livrabil — problema noastră e că **uită** să acționeze, nu că nu pricepe. |
| Anti-pattern explicit (cod-în-chat ≠ livrabil) | Exact failure mode-ul observat în warmup. Numirea explicită îl scoate din "default behavior" al modelului. |
| Verify-then-emit gate cu `Read`/`ls` | Forțează un tool call înainte de închidere; modelul nu poate "uita" pentru că emiterea liniei finale depinde de această confirmare. Aceasta e diferența cheie față de `CONSILIUM_SUFFIX` (text-only, fără gate). |
| Retry o singură dată | Dacă primul Write a eșuat din motive accidentale (path typo în prompt, encoding) retry are sens; dacă eșuează a doua oară, e probabil o problemă reală (permisiuni, path invalid) → soft fail prin `deliverable_write_failed`. |
| Soft fail prin `notes` (nu hard error) | Nu blocăm deliberarea; o marcăm ca observabil în raport. Următoarele audituri pot folosi câmpul ăsta să prindă regresii sistemice. |
| Excepție `do_nothing` / `skipped` | Aliniat cu skip-ul existent din Step 7 (`SKILL.md:233`); evită Write-uri spurioase când deciziile sunt "no-op". |

### Poziționare în workflow

Step 6.5 vine **după** logging-ul de feedback (Step 6) pentru două motive:
1. Feedback-ul reflectă **decizia deliberării**, nu artefactele de execuție — trebuie logat indiferent dacă Write-ul reușește.
2. `deliverable_write_failed` poate fi adăugat în raport înainte de emiterea liniei finale (ordinea: log → write → verify → eventual notes-update → emit line).

Step 6.5 vine **înainte** de Step 7 (auto-pipeline) pentru că:
- Step 7 face inferență de "implement/compile/review/test" steps — dacă fișierele nu sunt scrise, restul pipeline-ului nu are sens.
- Step 7 rămâne opt-in / advisory; Step 6.5 e obligatoriu când contractul există.

---

## 2. benchmark-modes/run_task.py — cleanup

### Schimbarea

`run_task.py:77-84` — eliminare constantă `CONSILIUM_SUFFIX` (înlocuită cu comentariu de tracking):

```python
# CONSILIUM_SUFFIX removed (2026-05-18) — Step 6.5 in Consilium SKILL.md now
# enforces deliverable writes for any prompt that declares files. Keeping the
# suffix here would duplicate the contract across two sources of truth.
```

`run_task.py:519-521` — păstrăm `CLAUDE_HEADLESS=1` (folosit de Step 6 pentru `PEND_HEADLESS`), eliminăm append-ul de suffix:

```python
if args.mode.startswith("consilium_") and not args.manual:
    os.environ["CLAUDE_HEADLESS"] = "1"
    # (no suffix append — Step 6.5 in SKILL.md handles deliverable enforcement)
```

### Efecte colaterale

- **Fairness cross-mode crește.** `opus_bare` și `superpowers` nu primeau `CONSILIUM_SUFFIX`; doar `consilium_*` îl primea. Eliminându-l, toate modurile primesc același prompt baseline → comparația cross-mode devine mai curată.
- **Context size scade marginal** pentru consilium runs (~80 tokens). Nu măsurabil.
- **Single source of truth** pentru regulile de enforcement → modificările viitoare se fac într-un singur loc (SKILL.md).

---

## 3. Data flow (post-change)

```
┌─ User prompt (cu `**Required output files**: - `solution.py``)
│
▼
[Step 0-6 unchanged] — Conservator → Generator → Control → Aggregator → Report → Feedback log
│
▼
┌─ Step 6.5 ───────────────────────────────────────┐
│ scan task input for deliverable contract         │
│   ├─ found → for each declared filename:         │
│   │           Write(file_path, content)          │
│   │           Read(file_path) to verify          │
│   │           if missing → retry once            │
│   │           if still missing → notes update    │
│   └─ not found → no-op (skip to Step 7)          │
└──────────────────────────────────────────────────┘
│
▼
emit `chosen: <id> | conf: <X> | runs/<file>.json`
│
▼
[Step 7 unchanged, opt-in]
```

---

## 4. Error handling

| Failure mode | Behavior |
|---|---|
| Prompt fără declarație de fișier | No-op silent. Step 6.5 trece transparent. |
| `chosen_approach == "do_nothing"` sau `"skipped"` | No-op. Aliniat cu skip-ul existent din Step 7. |
| Write reușește, Read confirmă | Path normal; emit line. |
| Write eșuează prima dată | Retry o singură dată. |
| Write eșuează și a doua oară | Adaugă `deliverable_write_failed: <file>` în `notes`; emit line. **Nu** blochează deliberarea. |
| Filename ambiguu (multiple backticks pe aceeași linie) | Modelul ia primul backticked token după `-`/`*` ca filename, restul ca context. Edge case rar; dacă apare, raportabil în notes. |
| Path conține `..` sau e absolut | Filename trebuie să fie relativ la `cwd`. Dacă promptul cere path absolut sau cu `..`, e probabil o eroare în prompt — model raportează în notes ca `invalid_deliverable_path` și nu scrie. |

---

## 5. Testing plan

### T1 — Caz regresat (priority 1)
```powershell
cd C:\Users\ALEX\Desktop\Doc\benchmark-modes
python run_task.py --mode consilium_sequential --task code/00_warmup --clean
```
**Expected:**
- `workspace/consilium_sequential/code/00_warmup/solution.py` există pe disc
- `verify/report.json` = `{"ok": true, "kind": "pytest", "passed": 8, "total": 8, ...}`
- `RESULT.md` arată `Score: 60 / 60`

### T2 — Outlier `01_car_wash.md` (priority 1)
```powershell
python run_task.py --mode consilium_sequential --task reasoning/01_car_wash --clean
```
**Expected:** `workspace/.../reasoning/01_car_wash/answer.md` cu prima linie `ANSWER: C`. Cazul cel mai sensibil pentru trigger-ul comportamental (singura formulare inline).

### T3 — No-regression pe consilium non-deliverable (priority 2)
Sesiune interactivă manuală în repo-ul Consilium:
```
/consilium  pe un diff existent fără cerere de fișiere
```
**Expected:** Step 6.5 trece silent (zero Write calls); deliberarea se închide normal. Validează că regula e cu adevărat opt-in pe contract.

### T4 — Cross-mode sweep (priority 3, cost ~$3-5)
După ce T1+T2 trec:
```powershell
foreach ($mode in 'consilium_sequential','consilium_trias','consilium_dialectic') {
  foreach ($task in 'code/00_warmup','code/01_circuit_breaker','reasoning/01_car_wash','reasoning/02_sprint_collapse') {
    python run_task.py --mode $mode --task $task --clean
  }
}
```
**Expected:** toate 12 runs au deliverable pe disc; comparativ cu baseline-ul anterior.

### T5 — `do_nothing` short-circuit (priority 3, smoke-test artificial)
Prompt artificial: `"Codul există deja; nu modifica nimic. **Required output files:** - `noop.py``"`.
**Expected:** `chosen_approach == "do_nothing"` → `noop.py` **nu** se creează; raport curat fără `deliverable_write_failed`.

### Self-improvement loop (obligatoriu per CLAUDE.md)
Înainte de commit final: `/consilium` pe diff-ul SKILL.md ca să nu introducă regresii pe deliberările viitoare. Run salvat în `runs/`, logat în `FEEDBACK.html` via `log_feedback.py`.

---

## 6. Risks & mitigations

| Risc | Severitate | Mitigation |
|---|---|---|
| Modelul ignoră Step 6.5 ca a ignorat `CONSILIUM_SUFFIX` | High | **Verify gate** (Read + emit-only-after-verified) închide loop-ul — diferența cheie față de suffix. |
| Trigger comportamental detectează fals pozitiv (scrie fișiere nedorite) | Medium | Skill rule cere "explicit declarat de user să livreze"; restul fișierelor menționate (ex: `\`priors.py\``) sunt referințe, nu deliverables. Antrenamentul modelului face distincția. T3 validează. |
| Regresie pe consilium real (non-benchmark) | Medium | Step 6.5 e no-op fără declarație de fișier. T3 validează explicit. |
| Atingerea SKILL.md crește `regression_risk` per CLAUDE.md | Medium | Self-improvement loop obligatoriu — `/consilium` rulat pe schimbare înainte de commit. |
| Outlier `01_car_wash.md` (inline phrasing) nu e prins de model | Medium | T2 e priority 1 exact pentru asta. Dacă T2 eșuează, opțiunile sunt: (a) adăugăm explicit "save to <file>" în trigger comportamental, sau (b) acceptăm că outlierul rămâne neacoperit până cineva editează prompt-ul (separat de scope-ul prezent). |
| Filename relative path vs `cwd` greșit | Low | Skill-ul rulează cu `cwd=workspace`; filename rezolvă relativ corect. Documentat explicit. |

---

## 7. Files touched

| Fișier | Schimbare | Linii afectate |
|---|---|---|
| `C:\Users\ALEX\Desktop\Doc\Consilium\SKILL.md` | Insert section "### 6.5. Deliverable contract enforcement (auto)" între linia ~199 (sfârșit Step 6) și ~201 (început Step 7) | +~35 linii |
| `C:\Users\ALEX\Desktop\Doc\benchmark-modes\run_task.py` | Elimină constantă `CONSILIUM_SUFFIX` (77-84) + append-ul (519-521) | -~15 linii / +3 comentariu |
| `C:\Users\ALEX\Desktop\Doc\Consilium\docs\superpowers\specs\2026-05-18-deliverable-enforcement-design.md` | Acest spec | +~250 linii (artefact) |

**Prompt-uri benchmark — neatinse** (per cerința user).

---

## 8. Open questions / Decisions taken

| Question | Decision | Rationale |
|---|---|---|
| Trigger strict (header only) vs mediu (orice marker) vs lax (orice fișier menționat)? | Mediu (orice prompt cu declarație explicită) | User answer, sesiune brainstorming. Blast radius mic + opt-in clar. |
| Fix in SKILL.md vs run_task.py vs ambele? | SKILL.md only | User answer. Single source of truth. |
| Modifică prompts/reasoning/01_car_wash.md ca să normalizeze formatul? | NU | User explicit: "nu vreau să fie schimbate problemele". Trigger comportamental acoperă outlierul. |
| Step nou (6.5) sau extindere Step 7? | Step nou (6.5) | Step 7 e opt-in / advisory; enforcement-ul e obligatoriu. Concerne separate. |
| Hard fail sau soft fail pe Write eșuat? | Soft fail prin `notes` | Nu blocăm deliberarea pentru o problemă posibil tranzitorie; observabil în raport pentru audit. |
