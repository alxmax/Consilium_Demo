---
name: consilium
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, or when uncertain between multiple implementation approaches.
---

# Consilium — Code Deliberation Skill

Pattern de deliberare multi-perspectivă pentru orice modificare de cod. Trei voci independente colaborează pentru a evalua o schimbare:

- **Generator** (creativ) — propune alternative, divergent thinking
- **Control** (analitic) — verifică corectitudine tehnică
- **Conservator** (prudent) — evaluează risc și reversibilitate

## Constitution

Patru principii care guvernează **fiecare** deliberare. Au prioritate când o voce dă o recomandare ce intră în conflict cu ele.

1. **Think before coding.** Expune tradeoff-urile explicit. Dacă requestul are 2 interpretări plauzibile, listează-le ca `candidates` separate — nu alege tăcut.
2. **Simplicity first.** Minimum de cod. Refuză abstracții speculative și feature-uri nesolicitate. `do_nothing` e întotdeauna în lista de candidați.
3. **Surgical changes.** Atinge doar ce cere goal-ul. Conservator-ul măsoară devierea prin `scope_drift` — respectă un scor mare.
4. **Goal-driven execution.** Restate goal-ul ca **success criterion** testabil înainte de Generator. Output-ul final include un pas de **verification**.

*(Adaptat după CLAUDE.md al lui Andrej Karpathy, via [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).)*

## When to use

Activează acest skill când:
- Faci **review de PR** sau diff
- Planifici un **refactor** care atinge 2+ fișiere
- Trebuie să alegi între **mai multe abordări**
- Ești pe punctul de a face **commit pe cod shared/core**
- Vrei o **assessment de risc** înainte de a accepta o sugestie

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach".

## Workflow

### 0. Bootstrap (înainte de orice grep / Read pe codebase)
Două acțiuni în ordine:

1. **Citește contractele celor 3 voci** — `prompts/generator.md`, `prompts/control.md`, `prompts/conservator.md`. Definesc câmpurile exacte produse de fiecare voce. **Notă parallel/dialectic:** conținutul fiecărui prompt trebuie *inline-uit* în dispatch-ul sub-agentului — citirea la Step 0 nu e suficientă.
2. **Rulează `python scripts/priors.py`** — întoarce priori soft din `FEEDBACK.html` + `runs/`. Dacă `stale_pendings` e non-empty, oprește și întreabă: *"Ai N entries PEND vechi: [date | chosen] × N. Vrei să le închid (OK/BAD/skip)?"* Actualizează cu `Edit` pe `FEEDBACK.html` (înlocuiește `PEND` cu `OK`/`BAD`), **nu** cu `log_feedback.py`. Dacă `pend_pressure > 0.5`, adaugă alertă: *"Atenție: {pend_count}/{window_size} entries recente sunt PEND — consideri să le închizi?"* (soft, nu bloca deliberarea).

### 1. Gather context & state the goal
Citește schimbarea propusă. Identifică scope (fișiere, module, linii), tip (bugfix/feature/refactor/cleanup), blast radius. Formulează `success_criterion` — o propoziție testabilă.

**Clarity gate.** Înainte de Generator: *poți scrie 2+ interpretări plauzibile distincte?* Dacă da — Stop, listează-le, întreabă care e reală. Semnale roșii: verbe vagi fără obiect concret, referințe nedezambiguate, scope implicit, limite lipsă. Dacă toate sunt clare → continuă fără să întrebi.

### 1.5. Scope gate (auto)
```bash
python scripts/scope_gate.py            # working tree vs HEAD
python scripts/scope_gate.py --ref main # main..HEAD
```
Dacă `should_skip: true`, emite raportul minimal și oprește:
```json
{
  "success_criterion": "...", "verification": "...",
  "chosen_approach": "skipped", "skipped": true,
  "skip_reason": "...", "signals": {"files_changed": 1, "lines_changed": 4, "blocklist_hits": []},
  "voice_scores": null, "confidence": null, "alternatives": [], "deliberation_log": []
}
```
Defaults: `max_files=1`, `max_lines=15`, blocklist conservativ (`auth/`, `security/`, `migrations/`, `.github/workflows/`, `**/secrets*`, `.env*`, `Dockerfile`, `*.tf`, fișiere dependențe). Override via `scope_gate.json` (`{max_files, max_lines, blocklist}`). Escape hatch: `CONSILIUM_FORCE_FULL=1` forțează `should_skip=false`. Gate **eșuează deschis** (no repo / bad ref → `should_skip: false`).

**Task-uri non-diff** (audit, architecture review, planning): scope_gate e no-op — poți sări Step 1.5.

### 2. Generator — produce alternative
Folosește `prompts/generator.md`. Cere **3–5 candidate**, inclusiv `do_nothing`. Stil divergent.

Output per candidate: `{id, summary, sketch, rationale}`. Adversarial e condiționat (clarity gate a returnat 2+ interpretări SAU schimbarea atinge shared/core code) — altfel emit `"adversarial_skipped": "<reason>"`.

### 3. Control — verifică corectitudine
Folosește `prompts/control.md`. Per candidate: types, logică, tests, style.

Output: `{id, valid: bool, issues: [...], tests_to_write: [...]}`. `tests_to_write` obligatoriu pentru `valid: true` (excepție `do_nothing`) — 1-4 teste de acceptanță.

**Sequential:** rulează `python scripts/strip_context.py --for control` pe output-ul Generator înainte de a-l trimite Control.

### 4. Conservator — assess risc
Folosește `prompts/conservator.md`. Per candidate **valid**, scorează 4 factori (0.0–1.0):
- `diff_size` — dimensiunea brută a schimbării
- `scope_drift` — atinge zone nelegate de goal
- `regression_risk` — probabilitate de a sparge ceva funcțional
- `reversibility` — cât de greu revii dacă merge prost

Output: `{id, risk_score: 0.0–1.0, factors: {...}, rollback_recipe: [...]}`. `rollback_recipe` obligatoriu dacă `risk_score >= 0.3` — 2-5 pași concreți executabili fără context suplimentar.

**Aggregation rule:** `risk_score` = media celor 4 factori — **excepție: dacă `reversibility > 0.7`, `risk_score` nu poate cădea sub `reversibility`** (irreversibilitatea domină și previne diluarea prin media celorlalți factori).

**Sequential:** rulează `python scripts/strip_context.py --for conservator` pe outputs Generator + Control.

**Opțional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Ancorează `diff_size` la `files_changed/lines_*` și `regression_risk` la distribuția de churn când prezent.

### 5. Aggregate
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — veto la `risk_score > 0.7`; ranking prin medie ponderată `(generator + control + safety)` unde `safety = 1 - conservator`. La egalitate câștigă candidatul mai sigur. Alternativă: `--scheme risk_adjusted_utility` (penalty sigmoidal, fără veto rigid).

### 5b. Confidence
```bash
echo '{"candidates": [...], "chosen": "approach_id"}' | python scripts/confidence.py
```
Returnează `{confidence, agreement, separation}`. Dacă `chosen` e `null` (toți vetoiți), `confidence` e `null`.

### 6. Report
```bash
cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
```
Bundle schema: `{success_criterion, verification, generator, control, conservator, aggregate, confidence, telemetry}`. `build_report.py` derivă `voice_scores`, asamblează `alternatives` (cu `why_not`) și `deliberation_log`.

**Output JSON** (câmpuri obligatorii — validate de `validate_report.py`, cerute de Principle #4):
```json
{
  "success_criterion": "<string — propoziție testabilă>",
  "chosen_approach": "<id din candidates | null>",
  "verification": "<comandă sau check concret>",
  "alternatives": [{"id": "...", "summary": "...", "why_not": "..."}],
  "voice_scores": {"generator": 0.0, "control": 0.0, "conservator": 0.0},
  "confidence": 0.0,
  "deliberation_log": [{"step": "generator|control|conservator|aggregate", "...": "..."}]
}
```

**Terminal output discipline.** Nu scrie bundle-uri intermediare JSON pe disc (`bundle_*.json`). Piped-ază output-urile direct. Singurul output vizibil în terminal la final:
```
chosen: <id> | conf: <X> | runs/<file>.json
```

**Gate de validare** (obligatoriu înainte de a considera raportul final):
```bash
cat runs/<file>.json | python scripts/validate_report.py
```
Exit 0 = OK. Exit 1 = field lipsă/gol sau telemetry malformat. Exit 2 = JSON malformat.

**Acțiuni finale (obligatorii — fără ele deliberarea nu e completă):**
1. **Persistă raportul** în `runs/YYYY-MM-DD_HHMM_<label>.json`.
2. **Loghează în `FEEDBACK.html`** (confidence-gated):
   - `confidence >= 0.7` → `python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/<file>.json < runs/<file>.json`
   - `confidence < 0.7` → întreabă: *"Confidence sub prag (`<X>`). Vrei să override-ezi `<chosen>`? Alternative: `<alt_ids>`. Răspunde alt_id, 'no', sau 'skip'."* Apoi: `no` → `--outcome OK`; `<alt_id>` → `--outcome OVR --override-target <alt_id>`; `skip` → fără flag (PEND).
   - `confidence null` (toți vetoiți) → `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json`
   - **Windows note:** Folosește `python -X utf8` sau piped-ează direct din fișier — PowerShell `Get-Content | ...` adaugă BOM care sparge `json.load(sys.stdin)`.

## Skill maintenance

Aplică doar când editezi skill-ul (`scripts/*.py`, `prompts/*.md`, `SKILL.md`), nu la fiecare deliberare.

**Eval harness** — la editarea `aggregator.py`, `confidence.py`, `validate_report.py`, `strip_context.py` sau `dialectic_merge.py`:
```bash
python scripts/run_evals.py
```
17+ scenarii. Exit 0 = toate trec; non-zero = regresie.

**Usage rollup** (când ai 10+ runs cu telemetry): `python scripts/usage.py [--last 50]`

**Audit periodic feedback**: `python scripts/feedback.py [--recent 10 --runs]`

## Resources

| Script | Rol |
|---|---|
| `scripts/priors.py` | Priori soft din FEEDBACK.html + runs/ (Step 0) |
| `scripts/scope_gate.py` | Auto-detect skip dacă scope e mic (Step 1.5) |
| `scripts/probe_change.py` | Ancorare diff_size la `git diff --numstat` (Step 4) |
| `scripts/aggregator.py` | 4 scheme de voting + auto-relax la veto total (Step 5) |
| `scripts/confidence.py` | Derivă confidence din variance + separation (Step 5b) |
| `scripts/build_report.py` | Asamblează raportul canonic din bundle (Step 6) |
| `scripts/validate_report.py` | Gate Principle #4: success_criterion + verification + chosen_approach |
| `scripts/log_feedback.py` | Auto-append în FEEDBACK.html la finalul Step 6 |
| `scripts/strip_context.py` | Proiectează output voce anterioară la minim (Steps 3-4 sequential) |
| `scripts/dialectic_merge.py` | Combină Pass-1 + Pass-2 în payload aggregator-ready |
| `scripts/personalities.py` | Rejection sampling pentru ensemble mode |
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite scripturi deterministe |
| `scripts/usage.py` | Rollup telemetry din runs/ |
| `agents/consilium-subagent.md` | Subagent pentru invocare izolată via `Agent(subagent_type="consilium-subagent", ...)` |

## Feedback loop

- **`runs/`** — JSON per deliberare în `runs/YYYY-MM-DD_HHMM_<label>.json` (schema în `runs/README.md`). Gitignored. Citit de `priors.py` (Step 0), `usage.py`, `feedback.py`.
- **`FEEDBACK.html`** — o linie per folosire: `data | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. Local, gitignored. **Drill-down:** când `log_feedback.py` appendează, rows existente pierd drill-down-ul; folosește `migrate_feedback_md_to_html.py` pentru re-populare în bulk.

## Parallel voices mode

**Default-ul e parallel.** Dispatch cele 3 voci ca sub-agenți independenți — elimină cross-contamination complet.

**Notă:** `consilium-subagent` rulează **întotdeauna sequential** — dispatch-uiește cu `subagent_type=general-purpose` când vrei paralelism real.

### Cum (2 turns)
1. **Turn 1:** dispatch Generator (1 Agent call). Aștepți candidates.
2. **Turn 2:** dispatch Control + Conservator în paralel (2 Agent calls în același message), ambii primind candidates din Turn 1.
3. Rulează `dialectic_merge.py` cu `pass2` omis — normalizează control_score pentru candidates invalide. Schema input:
   ```json
   {"pass1": {"generator": {"candidates": [...]}, "control": {"verdicts": [...]}, "conservator": {"scores": [...]}}}
   ```
4. Agregi cu `scripts/aggregator.py`.

Fiecare sub-agent primește: `success_criterion`, diff/context, **conținutul integral al prompt-ului vocii sale**, instrucția de a returna strict JSON.

**Model default: Sonnet 4.6.** Dispatch explicit cu `model: "sonnet"`. Override: `model: "opus"` pe Generator pentru high-stakes/ambigue; `model: "haiku"` pe Control/Conservator pentru diff-uri mici. Fără override, vocile moștenesc modelul orchestratorului — setează explicit.

**Prompt template:**
```
Goal: <success_criterion>
Change under review: <diff sau descriere>
Codebase context: <fișiere atinse, limbaj, framework>

Your role and instructions:
<conținutul integral al prompts/<voice>.md>

Return STRICTLY the JSON specified in the "Output format" section above. No prose before or after.
```

**Skip parallel dacă:** schimbarea e trivială (<10 linii), nu ai tool-ul `Agent`, sau vrei să auditezi raționamentul pas-cu-pas.

## Sequential mode (structured single-pass)

**Nu este defaultul.** Sequential = același context pentru toate 3 vocile. Valoarea: **template-ul forțat** — produce `rollback_recipe`, `tests_to_write`, `success_criterion` structurat chiar fără sub-agenți. Folosește `strip_context.py` la Steps 3-4 pentru a reduce parțial contaminarea.

**Alege sequential când:** scope_gate a dat skip dar vrei structura output-ului; nu ai `Agent` disponibil; vrei raționamentul pas-cu-pas vizibil în context.

**Nu livrează:** independență reală între voci, garanție anti-sycophancy, 3 perspective cu adevărat separate.

## Dialectic mode (opt-in, two-pass)

Two-pass: Pass 1 = parallel; Pass 2 = fiecare voce revizuiește văzând output-urile celorlalte două. Cost: 2× parallel. Implementat în `scripts/dialectic_merge.py`.

## Ensemble mode (opțional)

Pentru high-stakes (migrări DB, security, refactor mare):
```bash
python scripts/personalities.py 5
```
Generează N=4–6 personalități cu weights random `w ∈ [0.2, 0.49]`. Rulează skill-ul de N ori, agregă cu `--scheme weighted`.
