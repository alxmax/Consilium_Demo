---
name: consilium
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, before implementing non-trivial features (to catch missing tests and prevent code loss), or when uncertain between multiple implementation approaches.
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

## When to use

Activează acest skill când:
- Faci **review de PR** sau diff
- Planifici un **refactor** care atinge 2+ fișiere
- Trebuie să alegi între **mai multe abordări**
- Ești pe punctul de a face **commit pe cod shared/core**
- Vrei o **assessment de risc** înainte de a accepta o sugestie
- Ești pe punctul de a **implementa** o funcționalitate non-trivială (>1 fișier sau >30 linii)
- Vrei să verifici că o implementare completă nu a pierdut funcționalitate existentă, edge case-uri sau teste

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach", "before implementing", "implement feature", "code quality", "missing tests".

## Workflow

### 0. Bootstrap (înainte de orice grep / Read pe codebase)
Două acțiuni în ordine:

1. **Citește contractele celor 3 voci** — `prompts/voices/generator.md`, `prompts/voices/control.md`, `prompts/voices/conservator.md`. Definesc câmpurile exacte produse de fiecare voce. **Notă parallel/dialectic:** conținutul fiecărui prompt trebuie *inline-uit* în dispatch-ul sub-agentului — citirea la Step 0 nu e suficientă.
2. **Rulează `python scripts/priors.py`** — întoarce priori soft din `FEEDBACK.html` + `runs/`. Trei câmpuri ne pot bloca deliberarea curentă până sunt rezolvate:
   - `stale_pendings` non-empty (PEND mai vechi de 2 zile): întreabă *"Ai N entries PEND vechi: [date | chosen] × N. Vrei să le închid (OK/BAD/skip)?"* — actualizează cu `mark_outcome.py --date <d> --chosen <id> --outcome OK|BAD` (preferat) sau cu `Edit` direct pe `FEEDBACK.html`. **Nu** folosi `log_feedback.py` — duplichează rândul. **Headless** (`is_headless()`): loghează `[priors] stale_pendings: N entries — skipping prompt` pe stderr și continuă fără să întrebi.
   - `missing_feedback_runs` non-empty: rulează `python scripts/audit_feedback.py --backfill` ca să creezi PEND-uri pentru runs orfane, apoi rezolvă-le ca mai sus. Dacă lista e mai mare de 3, prefer să rezolvi gap-ul *înainte* de a începe o deliberare nouă. **Headless**: rulează `audit_feedback.py --backfill` automat și continuă.
   - `pend_pressure > 0.3` (raportul PEND în ultimele N=20 entries — pragul a scăzut de la 0.5): alertă soft *"{pend_count}/{window_size} entries recente sunt PEND — consideri să le închizi?"* — nu bloca, dar înregistrează semnalul. **Headless**: log only, no prompt.

   **Headless (non-interactiv — `claude -p` sau CI):** `stale_pendings` și `missing_feedback_runs` sunt suprimate automat (returnate `[]`) când `sys.stdin.isatty()` e `False`. Override explicit: flag `--headless` sau env var `CONSILIUM_HEADLESS=1`. Output include `headless_mode: true` ca marcaj pentru consumatori.

### 1. Gather context & state the goal
Citește schimbarea propusă. Identifică scope (fișiere, module, linii), tip (bugfix/feature/refactor/cleanup), blast radius. Formulează `success_criterion` — o propoziție testabilă.

**Clarity gate.** Înainte de Generator: *poți scrie 2+ interpretări plauzibile distincte?* Dacă da — Stop, listează-le, întreabă care e reală. Semnale roșii: verbe vagi fără obiect concret, referințe nedezambiguate, scope implicit, limite lipsă. Dacă toate sunt clare → continuă fără să întrebi. **Excepție non-interactivă (subagent):** nu poți întreba utilizatorul — emite fiecare interpretare ca Generator candidate cu prefix `interp_a_*`, `interp_b_*` și documentează ramificațiile în `subagent_notes.clarity_branches`.

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

### 2. Conservator — assess risc (runs FIRST)
Folosește `prompts/voices/conservator.md`. Rulează **înainte** de Generator și Control. Output-ul setează `tokens_budget` pentru celelalte voci.

Required Questions (Q1-Q5): reversibility, magnitude, counterparty_risks, status quo bias check, meta_recommendation.

Output per candidate: `{id, regression_risk: {reversibility, magnitude, net_concern}, counterparty_risks, bias_check, meta_recommendation, tokens_budget: {generator, control}, irreversibility_flag, rollback_recipe, notes}`.

**Sequential-first.** Conservator runs before Generator and Control. Its `tokens_budget` output caps how deep the other voices go. Its `irreversibility_flag: true` BLOCKS the pipeline — confirm user consent before proceeding.

**Veto check (auto, after Conservator output):**
- If `irreversibility_flag: true` → stop, ask user: *"Conservator marcheaza aceasta decizie ca ireversibila. Confirmi ca vrei sa continui?"* — proceed only with explicit YES. **Headless** (`is_headless()`): NU bloca; setează `metadata.headless_overridden: true` în bundle și continuă. Orchestratorul extern care a setat `CLAUDE_HEADLESS=1` și-a asumat stake-ul.
- If `meta_recommendation: scale_down` → skip Generator's unconventional/adversarial candidates; cap at 2 candidates; use short path.
- If `meta_recommendation: scale_up` → warn user, add context request before Generator. **Headless**: warning emis pe stderr, contextul nu poate fi cerut interactiv — continuă cu input-ul existent.

**Opțional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Ancorează `magnitude` la `files_changed/lines_*` și `regression_risk.net_concern` la distribuția de churn când prezent.

### 3. Generator — produce alternative
Folosește `prompts/voices/generator.md`. Cere **3–5 candidate**, inclusiv `do_nothing`. Stil divergent. Respectă `tokens_budget.generator` setat de Conservator.

Output: `{candidates: [{id, summary, sketch, rationale, downside_estimate}], fallback_scenario, coverage_check, challenge_upward, abstain, preferred}`. Adversarial e condiționat (clarity gate a returnat 2+ interpretări SAU schimbarea atinge shared/core code) — altfel emit `"adversarial_skipped": "<reason>"`.

**Receives from Conservator (selective):** `magnitude`, `counterparty_risks`, `tokens_budget.generator`. Does NOT receive `meta_recommendation` — that is policy, not Generator input.

**Challenge upward:** If Generator sets `challenge_upward.triggered: true`, re-run Conservator with Generator's context before proceeding to Control.

### 4. Control — verifică corectitudine
Folosește `prompts/voices/control.md`. Per candidate: types, logică, tests, style.

Required Questions (Q1-Q4): glossary (max 5), hidden_assumptions (max 3), disagreements, fixed/negotiable_constraints.

Output: `{glossary, hidden_assumptions, disagreements, fixed_constraints, negotiable_constraints, glossary_fail, glossary_attempts, verdicts: [{id, valid, issues, tests_to_write, notes}]}`. `tests_to_write` obligatoriu pentru `valid: true` (excepție `do_nothing`) — 1-4 teste de acceptanță.

**Receives from both:** full Conservator output + full Generator output.

**Post-Control veto check:**
- If `glossary_fail: true` → BLOCK, request reformulation from user.
- If `disagreements` contains any `type: substantial` → REWORK: re-run Generator with clarification before aggregating.

### 5. Aggregate
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — veto la `risk_score > 0.8`; ranking prin medie ponderată `(generator + control + safety)` unde `safety = 1 - conservator`. La egalitate câștigă candidatul mai sigur. Alternativă: `--scheme risk_adjusted_utility` (penalty sigmoidal, fără veto rigid).

### 5b. Confidence
```bash
echo '{"candidates": [...], "chosen": "approach_id"}' | python scripts/confidence.py
```
Returnează `{confidence, agreement, separation}`. Dacă `chosen` e `null` (toți vetoiți), `confidence` e `null`.

> **Calibrare (audit R2 2026-05-17):** `agreement` măsoară divergența între roluri în cadrul UNUI run — nu stabilitatea inter-run. Scorurile Conservator sunt ancorate prin formulă categorică (vezi `conservator.md`); scorurile Generator/Control sunt float-uri self-assigned neancorate. Un al doilea run cu același input poate produce scoruri diferite (pstdev estimat 0.12–0.18 pe `risk_score`). Valoarea `confidence` nu e o probabilitate calibrată — e un semnal de consistență internă.

**Quoting:** Evită construirea de Python inline via `-c "..."` cu payload JSON — apostrofurile din cod pot rupe quoting-ul bash. Folosește pipe pe stdin (ca mai sus) sau flag-ul `--input <file>`.

### 5c. Meta-critic (auto, advisory)
```bash
cat bundle.json | python scripts/meta_critic.py
```
Scorează **calitatea deliberării** (nu corectitudinea alegerii): `generator_divergence` (paraphrasing?), `control_concreteness` (speculation?), `conservator_spread` (shrug?). Emite `deliberation_quality.flags` — atașează la bundle înainte de Step 6 (build_report îl pasează în raport). `flags` non-empty nu blochează, dar trebuie menționate în `reasoning`.

### 5d. Retry on low confidence (opțional, single pass)
Dacă `confidence < 0.7`, **înainte** să întrebi utilizatorul:
```bash
cat bundle.json | python scripts/retry_context.py
```
Returnează top-2 candidați cu fișiere/simboluri de citit/grepat. Folosește hint-urile → gather context (Read + Grep) → re-rulează Generator/Control/Conservator **o singură dată** cu input îmbogățit. Dacă confidence încă < 0.7, abia atunci întrebi utilizatorul (Step 6).

**Headless** (`is_headless()`): skip Step 5d integral — merge direct la Step 6 unde `PEND_HEADLESS` e logat. Notă empirică: `retry_context.py` are zero labeled usage în corpus `runs/` (vezi audit senate `2026-05-16_220025-flow-and-modes-audit-r2`); skip-ul în headless e aliniat cu acel deletion-vote și nu pierde un mecanism activ.

### 6. Report

**Telemetry emission (obligatoriu — înainte de `build_report.py`).**

La fiecare dispatch (voce sau senator), imediat după return, acumulează în bundle:

- `telemetry.voices.<voice_name>` sau `telemetry.senators.<senator_name>` (Senate): `{tokens_in: ceil(len(prompt)/4), tokens_out: ceil(len(response)/4), latency_ms: <wall-clock>}` — prompt = text complet trimis (persona + context + propunere, nu doar propunerea).
- Suma tokens + latency per voce dacă există retry-uri pe același dispatch.
- `telemetry.mode` ← label canonic (`"sequential"`, `"senate"`, `"trias"` etc. — din `## Dispatch defaults`).
- `telemetry.dispatch_count` ← total dispatch-uri (inclusiv retry-uri).

De ce obligatoriu: `scripts/efficiency.py` returnează `null` pentru orice run fără telemetry, poluând mediile per mod — un run fără telemetry e invizibil în comparațiile de eficiență.

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

**Acțiuni finale (obligatorii — deliberarea nu e completă fără ele):**

Cele două apeluri de mai jos sunt **obligatorii**. Dacă orchestratorul oprește înainte de a le rula, raportul există pe disc dar e invizibil pentru priors → următoarea deliberare nu va beneficia de feedback-ul ăsta. Audit periodic: `python scripts/audit_feedback.py` listează runs orfane; cu `--backfill` adaugă rânduri PEND default.

1. **Persistă raportul** în `runs/YYYY-MM-DD_HHMM_<label>.json`.
2. **Loghează în `FEEDBACK.html`** (confidence-gated, fără să sări vreun caz):
   - `confidence >= 0.7` → `python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/<file>.json < runs/<file>.json`
   - `confidence < 0.7` → întreabă: *"Confidence sub prag (`<X>`). Vrei să override-ezi `<chosen>`? Alternative: `<alt_ids>`. Răspunde alt_id, 'no', sau 'skip'."* Apoi: `no` → `--outcome OK --force-override`; `<alt_id>` → `--outcome OVR --override-target <alt_id>`; `skip` → fără flag (PEND, dar **nu lăsa apelul să fie sărit**).
   - `confidence null` (toți vetoiți) → `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json`
   - **Cale non-interactivă (headless — `claude -p`).** Sari promptul de la `confidence < 0.7` și apelează direct: `python -X utf8 scripts/log_feedback.py --outcome PEND_HEADLESS --run-path runs/<file>.json < runs/<file>.json`. `PEND_HEADLESS` e exclus structural din `pend_pressure` și `stale_pendings` (PEND_HEADLESS ≠ „PEND" în Counter) — nu necesită rezolvare manuală.

**Outcome confirmation (retroactiv).** Outcome-ul logat la pasul 2 e subiectiv — reflectă impresia imediată. Dacă mai târziu producția dezvăluie un regression sau o alegere bună, suprascrie-l cu marker confirmat:
```bash
python scripts/mark_outcome.py --run-path runs/<file>.json --outcome BAD --reason "broke prod migration"
```
Marker-ul `[confirmed]` apare în note; `priors.py` ponderează aceste rânduri 2x față de feedback-ul subiectiv (vezi `weighted_bad_rate`).

### 7. Auto-pipeline (opt-in, post-report)

După ce Step 6 e complet (raport salvat, feedback logat), poți infera și confirma pașii de implementare:

```bash
cat runs/<file>.json | python scripts/infer_pipeline.py          # interactiv
python scripts/infer_pipeline.py --input runs/<file>.json --yes  # CI/headless
python scripts/infer_pipeline.py --input runs/<file>.json --dry-run  # print only
```

Scriptul citește `chosen_approach`, `magnitude` și `reversibility` din raport și caută în tabelul de mai jos:

| magnitude | reversibility | pași inferați |
|---|---|---|
| trivial | complete | implement |
| trivial | partial | implement → compile |
| trivial | irreversible | implement → compile → test |
| moderate | complete | implement → compile |
| moderate | partial | implement → compile → test |
| moderate | irreversible | implement → compile → review → test |
| high/critical | orice | implement → compile → review → test |

**Definiții pași:**
- `implement` — Scrie codul per `chosen_approach`. Dacă prompt-ul conține o secțiune `**Required output files**` sau `**Deliverables**`, folosește Write tool pentru fiecare fișier declarat la calea specificată — nu emite implementarea doar ca fenced block în chat. Fișierele trebuie să existe pe disc, nu doar în răspuns.
- `compile` — rulează target-ul, verifică exit code 0 (runtime check)
- `review` — re-rulează Control voice pe codul efectiv scris (nu propunerea)
- `test` — rulează test suite existent (pytest/unittest autodiscovery)

Output JSON: `{"steps": [...], "rationale": {"chosen": "...", "magnitude": "...", "reversibility": "...", "lookup_key": "..."}}`.

Reject (`n` la prompt) → rejection logat în `runs/YYYY-MM-DD_HHMM_pipeline_rejected.json`. Rerun cu `--yes` pentru CI sau `--dry-run` pentru audit fără confirmare.

**Skip Step 7 dacă:** `chosen_approach` e `do_nothing` sau `skipped` (scriptul iese cu exit 1 și mesaj clar) — **SAU** `is_headless()` (orchestratorul extern decide pipeline-ul; sub-agentul Consilium nu execută implement/compile/test în context `claude -p`).

## Skill maintenance

Aplică doar când editezi skill-ul (`scripts/*.py`, `prompts/*.md`, `SKILL.md`), nu la fiecare deliberare.

**Eval harness** — la editarea `aggregator.py`, `confidence.py`, `validate_report.py`, `strip_context.py` sau `dialectic_merge.py`:
```bash
python scripts/run_evals.py
```

**Usage rollup** (când ai 10+ runs cu telemetry): `python scripts/usage.py [--last 50]`

**Audit periodic feedback**: `python scripts/feedback.py [--recent 10 --runs]` (stats), `python scripts/audit_feedback.py [--backfill]` (runs fără rând FB).

**Benchmarking discipline** — orice claim cantitativ pe comportamentul vocilor (`fab-rate`, `accuracy`, `catch-rate`) trebuie să citeze un **oracle independent** (al doilea expert SAU citation explicită din enunț/specs care fixează ground truth), nu quick-take-ul evaluatorului. Înainte de a publica rezultatele unui benchmark: pentru fiecare opțiune plauzibilă (A/B/C/D...), documentează explicit *"există citire alternativă a problemei în care răspunsul X devine corect?"* — răspuns explicit per opțiune. Verdict "fabricație" pe un raționament rămâne blocat până la oracle review separat de intuiția evaluatorului. Aplicată retroactiv: orice claim de fab-rate existent în `experiments/` și `runs/` se revizuiește prin această grilă. Checklist operațional: `experiments/README.md`. Origin: corigendum-ul P3 (vezi `experiments/p3-car-wash.html`) — oracle-ul greșit a inversat semantic concluzia "fabrication" → "real constraint catch".

## Resources

| Script | Rol |
|---|---|
| `scripts/priors.py` | Priori soft din FEEDBACK.html + runs/ (Step 0). Surface `missing_feedback_runs`, `stale_pendings` (prag 2 zile), `weighted_bad_rate`. |
| `scripts/scope_gate.py` | Auto-detect skip dacă scope e mic (Step 1.5) |
| `scripts/probe_change.py` | Ancorare diff_size la `git diff --numstat` (Step 4) |
| `scripts/aggregator.py` | 4 scheme de voting + auto-relax la veto total (Step 5) |
| `scripts/confidence.py` | Derivă confidence din variance + separation (Step 5b) |
| `scripts/meta_critic.py` | Scor calitate deliberare (divergence/concreteness/spread) — Step 5c |
| `scripts/retry_context.py` | Hint pentru single retry când confidence < 0.7 — Step 5d |
| `scripts/build_report.py` | Asamblează raportul canonic din bundle (Step 6) |
| `scripts/validate_report.py` | Gate Principle #4: success_criterion + verification + chosen_approach |
| `scripts/log_feedback.py` | Auto-append în FEEDBACK.html la finalul Step 6 |
| `scripts/mark_outcome.py` | Suprascriere outcome retroactiv (`[confirmed]` în note → pondere 2x) |
| `scripts/infer_pipeline.py` | Step 7: infer + confirmare pași de implementare din raport; `--dry-run` / `--yes` |
| `scripts/audit_feedback.py` | Listează runs fără rând FB; cu `--backfill` adaugă PEND default |
| `scripts/memory.py` | Read API uniform peste cele 3 tiers (short/medium/long) |
| `scripts/strip_context.py` | Proiectează output voce anterioară la minim (Steps 3-4 sequential) |
| `scripts/dialectic_merge.py` | Combină Pass-1 + Pass-2 în payload aggregator-ready |
| `scripts/personalities.py` | Trias mode — 3 personalități fixe cu weights + lens paths |
| `prompts/voices/skeptic.md` | Voce focală pentru flagul `skeptic_on_chosen` (composabil peste orice mod) — primește doar chosen, produce obiecție concretă sau `meta_scope_mismatch` |
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite scripturi deterministe |
| `scripts/usage.py` | Rollup telemetry din runs/ |
| `agents/consilium-subagent.md` | Subagent pentru invocare izolată via `Agent(subagent_type="consilium-subagent", ...)` |
| `prompts/senators/*.md` | 7 prompturi de audit pre-implementare (mod `senate`); fiecare cu specialitate distinctă (vezi tabelul din Senate mode) |
| `scripts/vocabulary_map.py` | RUND2: traduceri user-facing (reversibility/magnitude/meta_recommendation/verdict) + `compute_tokens_budget(magnitude, reversibility, meta)` |
| `scripts/senate_synth.py` | Synthesizer Senate: agregă 7 output-uri JSON → verdict `GO/MODIFY/STOP/DEEPLY_SPLIT/UNREACHABLE` + modify_requests + risks → salvează în `runs/senate/`. Suportă **multi-round (Laws 2+4)** via schema `{rounds: [...]}` cu `cross_questions[]`, `position_changes[]`, și `blocaj_resolution` (5-vote tiebreaker). **Law 3** (`blocaj_pending` advisory signal) activ pe ambele moduri când `verdict ∈ {MODIFY, DEEPLY_SPLIT}`. Backward compat pe legacy `{senators: {...}}`. |

## Feedback loop

- **`runs/`** — JSON per deliberare în `runs/YYYY-MM-DD_HHMM_<label>.json` (schema în `runs/README.md`). Gitignored. Citit de `priors.py` (Step 0), `usage.py`, `feedback.py`.
- **`FEEDBACK.html`** — o linie per folosire: `data | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. Local, gitignored. **Drill-down:** când `log_feedback.py` appendează, rows existente pierd drill-down-ul; folosește `scripts/deprecated/migrate_feedback_md_to_html.py` pentru re-populare în bulk (retired one-shot tool, see scripts/deprecated/).
- **Confirmed outcome.** `mark_outcome.py` adaugă marker `[confirmed]` în note. `priors.py` ponderează aceste rânduri 2x în `weighted_bad_rate`. Folosește când realitatea producției contrazice outcome-ul subiectiv din Step 6.

## Memory tiers

Consilium are 3 layere de memorie cu lifecycle diferit. `scripts/memory.py` oferă un read API uniform peste toate trei.

| Tier | Locație | Lifetime | Conținut | Citit de |
|---|---|---|---|---|
| **Short** | conversation window | sesiune | bundle în construcție (Steps 1–5b), clarity gate, success_criterion curent | doar agent (nepersistat) |
| **Medium** | `runs/*.json` | indefinit (gitignored) | un fișier per deliberare; episodic | `priors.py`, `usage.py`, `memory.py`, `audit_feedback.py` |
| **Long** | `FEEDBACK.html` + signals din `priors.py` | indefinit | un rând per folosire; agregat peste timp | `priors.py`, `feedback.py`, `memory.py`, `mark_outcome.py` |

CLI uniform:
```bash
python scripts/memory.py --tier medium --n 5             # ultimele 5 runs
python scripts/memory.py --tier long --query auth        # substring filter
python scripts/memory.py --tier all --query feedback     # union peste 3 tiers
```

## Headless invariants

Când `CLAUDE_HEADLESS=1` (set de orchestratorul extern care a invocat `claude -p`), 4 puncte din workflow renunță la prompt-urile user-facing și folosesc default-uri documentate. Pattern aliniat cu `CONSILIUM_FORCE_FULL` din `scope_gate.py`. Helper: `from utils import is_headless`.

| Step | Default headless |
|---|---|
| 0 (`stale_pendings`, `missing_feedback_runs`, `pend_pressure`) | log warning pe stderr + continuă; pentru `missing_feedback_runs` rulează `audit_feedback.py --backfill` automat |
| 2 (`irreversibility_flag: true`) | setează `metadata.headless_overridden: true` în bundle + continuă (orchestratorul extern și-a asumat stake-ul) |
| 5d (retry on low confidence) | skip integral; merge direct la Step 6 cu `PEND_HEADLESS` |
| 7 (auto-pipeline) | skip integral; orchestratorul extern decide implement/compile/test |

`is_headless() == False` (env var absent) → comportament curent neschimbat. Backward compat 100%.

**Pattern adopted:** boolean strict `CLAUDE_HEADLESS=1` (alte valori → False). Aliniat cu `CONSILIUM_FORCE_FULL=1` precedent (vezi `scripts/scope_gate.py`). Orchestratorul extern (run_task.py, CI script, parent agent) setează env var înainte de invocare; skill-ul nu modifică niciodată env-ul.

**Nota Senate:** `runs/senate/2026-05-18_164154-mode-bugfix-performance.json` + mini-senate H2+H4 (verdict B+X 5/7 + 4/7) au validat acest contract.

## Dispatch defaults (per voice / per senator)

Default behavior unless overridden by project memory (`MEMORY.md`). All voices și senatori pinned la `model: "sonnet"` per `feedback_subagents_sonnet.md`. Mode sections declare per-invocation overrides (e.g. `haiku` verifiers în `trias_split`, `opus` Generator pentru high-stakes) — single source of truth per mod, descriptive nu enforced.

Cost multipliers (baseline Sequential = 1×): Parallel 3× · Dialectic 6× · Trias 9× · `trias_split` 3.3× · Senate ~2.3× (7 senatori). Flagul `skeptic_on_chosen` adaugă +1 sub-agent peste modul de bază (ex: Parallel+flag = 1.33× Parallel, Dialectic+flag = ~2.3× Parallel).

## Parallel voices mode

<!-- === RUND2 === -->
**Parallel mode removed (RUND2).** Parallel dispatch is no longer a user-selectable option. Auto-triggered internally only when `magnitude = critical` AND `reversibility = irreversible`, as a cross-check on the sequential result. Every 20 runs, a silent parallel audit runs automatically; if systematic divergence is detected, frequency increases to 1/5.
<!-- === END RUND2 === -->

**Legacy reference (auto cross-check only).** Dispatch cele 3 voci ca sub-agenți independenți — elimină cross-contamination complet.

### Cum (2 turns)
1. **Turn 1:** dispatch Generator (1 Agent call). Aștepți candidates.
2. **Turn 2:** dispatch Control + Conservator în paralel (2 Agent calls în același message), ambii primind candidates din Turn 1.
3. Rulează `dialectic_merge.py` cu `pass2` omis — normalizează control_score pentru candidates invalide. Schema input:
   ```json
   {"pass1": {"generator": {"candidates": [...]}, "control": {"verdicts": [...]}, "conservator": {"scores": [...]}}}
   ```
4. Agregi cu `scripts/aggregator.py`.

Fiecare sub-agent primește: `success_criterion`, diff/context, **conținutul integral al prompt-ului vocii sale**, instrucția de a returna strict JSON.

**Override semantics (Parallel mode):** `model: "opus"` pe Generator pentru high-stakes/ambigue; `model: "haiku"` pe Control/Conservator pentru diff-uri mici. Default per `## Dispatch defaults`.

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

**Failure-mode recovery:**
- **Sub-agent crash / timeout:** retry acel Agent call o singură dată; la al doilea eșec, cade pe Sequential pentru vocea respectivă.
- **JSON malformat din voce:** respinge output-ul vocii, tratează ca lipsă (`{}` pentru verdicts/scores, sau `{"candidates":[]}` pentru generator) și continuă cu celelalte. Loghează eroarea în `deliberation_log` cu step `"<voice>_parse_error"`.
- **Câmpuri obligatorii lipsă (e.g. `candidates` empty):** ridică avertisment în terminal, sare aggregator-ul și emite raport skipped cu `skip_reason: "voice output incomplete after retry"`.
- **Strip_context**: necesar doar în modul Sequential (Steps 3-4); în Parallel fiecare voce rulează izolat și nu are nevoie de `strip_context.py`.

## Dialectic mode (opt-in, two-pass)

Two-pass: Pass 1 = parallel; Pass 2 = fiecare voce revizuiește văzând output-urile celorlalte două. Cost: 2× parallel. Implementat în `scripts/dialectic_merge.py`.

**Pass-2 schema (obligatorie per item).** Fiecare item Pass-2 (candidate / verdict / score) trebuie să emită fie `revision: <noul conținut>` fie `maintained: <motiv>`. Lipsa ambelor → `dialectic_merge.py` îl tratează ca dissent fallback și emite stderr warning (`[warning] dialectic pass-2 dissent fallback for <voice>: <ids>`). Candidate Pass-1 omise complet din Pass-2 generator declanșează `silently_dropped` warning și sunt recuperate din Pass-1.

Per-voice contract (prompt sursă: `prompts/voices/*_pass2.md`):

| Voce | Cheie output | Câmpuri obligatorii per item |
|------|-------------|------------------------------|
| Generator | `candidates[]` | `id` + (`revision` cu `summary/sketch/rationale` SAU `maintained` cu `reason`) |
| Control | `verdicts[]` | `id` + (`revision` cu `valid/issues` SAU `maintained` cu `peer_claim/dissent`) |
| Conservator | `scores[]` | `id` + (`revision` cu `what_changed/peer_evidence` SAU `maintained` cu `peer_claim/dissent`) |

Audit warnings la stderr după merge — verifică-le înainte să consideri 2× cost-ul justificat.

**Effort guidance în headless.** În `claude -p` (`is_headless()`), Pass-1 sub-agents pot rula la `effort=medium` — Pass-2 cross-review rămâne `high`. Decizia aparține orchestratorului extern care invocă `claude -p --effort medium`; skill-ul documentează posibilitatea, nu enforce-ază flag-ul CLI.

## Trias mode (high-stakes opt-in)

**Mecanica:** 3 personalități fixe (Pioneer / Architect / Steward) deliberează în paralel cu lens prompts injectate, fiecare aplicând weights diferite peste output. Vot democratic majoritar peste cele 3 chosen-uri.

### Când să folosești
- Schema/DB migration ireversibilă
- Security audit (auth, crypto, RCE potential)
- Refactor > 5 fișiere
- 2+ abordări arhitecturale plauzibile, fără clear winner
- Costul deciziei greșite >> costul rulării (9 sub-agenți, 3× Parallel)

### Workflow
1. Orchestrator citește `python -X utf8 scripts/personalities.py` — emite cele 3 personalități
2. Pentru fiecare personalitate, dispatch 3 voci (Gen/Ctrl/Cons) cu `prompts/<voice>.md` + `prompts/<personality>_lens.md` prepended
3. Personalitatea agregă voice scores cu weights proprii → `chose`
4. Orchestrator rulează `python -X utf8 scripts/aggregator.py --scheme team_vote` peste cele 3 chosen-uri
5. Confidence derivat din vote_pattern — pipe output-ul aggregator direct la `confidence.py`:
   ```bash
   echo '{"personalities":[...],"candidates":[...]}' | python scripts/aggregator.py --scheme team_vote | python scripts/confidence.py
   ```
   Nu construi manual `{"candidates":[...],"chosen":"..."}` pentru Trias — candidatele nu au `scores` per voce.

### Vote patterns
| Pattern | Confidence | Outcome |
|---|---|---|
| 3-0 | 0.95 | OK auto |
| 2-1 | 0.75 | OK auto |
| 2-0 | 0.70 | OK auto |
| 1-1-1 / 1-1-0 / 1-0-0 | null | PEND |
| 0-0-0 | null | PEND + retry_suggested |

### Failure recovery
- **1-1-1 fragmentation:** orchestrator întreabă user — accept one, re-run with constraints, or abort
- **0-0-0 total veto:** emite `retry_suggested` cu relaxed threshold sau Generator constraints

### Skip Trias dacă
- Diff < 20 lines / 1 fișier — `scope_gate.py` va skip oricum
- Conservatism strict cerut (Trias agregat e −18% Conservator)
- Bugfix evident — Sequential blind ajunge

## Trias split-model mode (`trias_split`)

**Mecanica:** Trias standard (3 personalități × 3 voci = 9 sub-agenți) cu override de model:
- **Generator voices** (1 per personalitate, 3 total) → Sonnet 4.6 (creativitate)
- **Control + Conservator voices** (2 per personalitate, 6 total) → Haiku 4.5 (verificare rapidă)

**Cost:** ~3.3× Parallel (vs 9× Parallel pentru Trias full).

### Când să folosești
- Decizii medium-stakes care beneficiază de diversitatea de personalități (3 perspective ortogonale) dar nu justifică costul Trias full
- Probleme unde verificarea e relativ surface-level (factor scoring, sanity checks) — Haiku ajunge
- Haiku verifiers: efect anti-zgomot pe probleme triviale fără constraint implicit (resping elaborări inutile), dar shallow-amplifier pe probleme cu constraint implicit — confirmă răspunsul evident fără să interogheze asumpția ascunsă (P3 corrigendum: 3/3 A pe o problemă cu răspuns corect C; vezi `experiments/p3-car-wash.html`). Nu folosi trias_split dacă problema poate conține constraints implicite — preferă Trias full sau `parallel + skeptic_on_chosen`.

### Workflow
Identic cu Trias standard, dar override-uri explicite la dispatch:
```
Pentru fiecare personalitate (Pioneer/Architect/Steward):
  Dispatch Generator: model="sonnet"
  Dispatch Control:    model="haiku"
  Dispatch Conservator: model="haiku"
```
Restul (vote pattern, confidence, failure recovery) identic cu Trias.

### Skip trias_split dacă
- Verificarea cere adâncime tehnică (security audit, schema migration complexă) — Haiku speculează, folosește Trias full
- Diff trivial — un mod simplu (Sequential/Parallel) ajunge
- Output schema strict required cu garanție 100% — Haiku violează ocazional instrucțiuni strict-JSON (vezi Run 1 lite_trias_A — disqualified for verbose output)

## Skeptic-on-chosen mode (`skeptic_on_chosen`)

**Mecanica:** `skeptic_on_chosen` este un **flag cross-cutting**, nu un mod fix. Se compune peste orice mod de bază (Sequential, Parallel, Dialectic, Trias): după ce modul de bază produce `chosen` și `confidence`, se dispatch-uiește 1 voce Skeptic suplimentară pe `chosen`-ul rezultat, cu prompt-ul `prompts/voices/skeptic.md`. Flagul rulează **secvențial post-hoc** pe orice mod (vs un mod fix care îl include în Pass-1). Nu există cod Python dedicat — orchestrarea se face prin dispatch standard al `prompts/voices/skeptic.md` cu chosen-ul curent.

**Cost:** +1 sub-agent față de modul de bază ales (indiferent care e acela). Ex: Parallel + flag = 4 sub-agenți (1.33× Parallel); Dialectic + flag = 7 sub-agenți (~2.3× Parallel).

> **Legacy note.** Modurile `parallel_skeptic` și `dialectic_skeptic` au fost moduri fixe distincte (Parallel/Dialectic cu Skeptic baked-in). Au fost colapsate în acest flag composabil pe 2026-05-17 — funcționalitatea identică se obține via `parallel + skeptic_on_chosen` și `dialectic + skeptic_on_chosen`. Numele vechi rămân în `validate_report.py` MODE enum pentru backward-compat cu runs istorice.

### Când să folosești
- Confidence-ul din modul de bază cade în banda `[0.5, 0.7]` — trigger **automat** (aggregator-ul poate semnala banda, orchestratorul aplică flagul)
- **Opt-in manual** via `--skeptic-on-chosen` când vrei un challenger focal post-hoc indiferent de confidence (medium-stakes, probleme cu constraint-uri implicite cunoscute)
- Probleme unde chosen_confirmation_pass a demonstrat valoare empirică — în special situații cu constraint-uri implicite nemenționate explicit în success_criterion (tip P3: precondițiile logice ale soluției nu apar în enunț)
- Când vrei challengerul focal pe orice bază (Sequential / Parallel / Dialectic / Trias) fără cost de mod fix dedicat
- Cazuri unde vrei să știi dacă chosen a ratat ceva, dar nu ai o bază de comparație (nu ai alternative viabile) — Skeptic-ul focal pe chosen e mai ieftin decât re-rularea întregii deliberări

### Workflow
1. Rulează modul de bază complet (oricare: Sequential / Parallel / Dialectic / Trias) → produce `chosen`, `confidence`, raport intermediar
2. Dacă `confidence ∈ [0.5, 0.7]` (auto) sau flagul `--skeptic-on-chosen` e activ, dispatch 1 sub-agent Sonnet 4.6 cu `prompts/voices/skeptic.md` inline + input minimal:
   ```
   chosen: <id, summary, sketch, rationale>
   success_criterion: <propoziția testabilă>
   verification: <comanda>
   ```
   NU pasezi alte candidate, scoruri sau log-uri de deliberare.
3. Validează skeptic output-ul:
   - `can_object: true` cu `concrete_concerns` ≥ 2 SAU `quoted_scenario` non-null → accept
   - `can_object: true` fără evidence → reject (schema fail), ship chosen original
   - `can_object: false` → ship chosen original, loghează că nu există obiecție concretă
4. Loghează rezultatul în `deliberation_log` cu step `"skeptic_on_chosen"` și setează flag `skeptic_caught_constraint: true|false` în raport
5. Aplică override semantics (secțiunea de mai jos)

### Override semantics
**Advisory by default.** Verdictul Skeptic-ului se loghează în `deliberation_log` ca entry cu step `"skeptic_on_chosen"` și flag `skeptic_caught_constraint: true|false`. `chosen` **nu se înlocuiește** — rămâne cel produs de modul de bază. Utilizatorul vede obiecția în raport și poate acționa sau ignora.

**Opt-in override via `--skeptic-can-override`.** Dacă flagul e activ ȘI Skeptic produce `addressable: requires_redesign`, verdictul Skeptic-ului supersedează `chosen`: orchestratorul prezintă utilizatorului alternativele din raport și întreabă dacă vrea să schimbe alegerea. Dacă Skeptic produce `addressable: in_place`, override-ul nu se aplică (advisory rămâne); dacă produce `addressable: unaddressable` cu `failure_mode: meta_scope_mismatch`, raportul e marcat `misapplied`.

Tabel sumar:

| Skeptic output | Advisory (default) | Cu `--skeptic-can-override` |
|---|---|---|
| `can_object: false` | ship chosen original | ship chosen original |
| `in_place` | log + nota în raport | log + nota în raport (fără override) |
| `requires_redesign` | log + advisory | orchestratorul propune alternativele |
| `unaddressable / meta_scope_mismatch` | marchează `misapplied` | marchează `misapplied` |

### Skip dacă
- Confidence ≥ 0.7 și flagul `--skeptic-on-chosen` nu e activ manual — Skeptic-ul n-are motivație structurală să găsească ceva
- Confidence < 0.5 — banda e prea jos pentru o singură voce challenger; escaladare la Trias sau user direct
- Diff e high-stakes intrinsec (auth, migrations, security) — folosește Trias full cu cost justificat

**Origine empirică.** Modul a apărut din analiza `experiments/p3-car-wash.html`: `chosen_confirmation_pass` (echivalentul conceptual al acestui flag) a atins catch-rate 100% în simulare și 4/7 în reruns reale pe P3 car wash — performanță superioară oricărui alt mod testat. Mecanismul: o singură voce skeptic pe `chosen` post-hoc obligă re-citirea success_criterion și detectarea constraint-urilor implicite ratate de toate vocile din Pass-1.

## Senate mode (`senate`)

**Scope:** `senate` are două moduri de invocare:
1. **Default (skill audit):** auditează modificări la skill-ul însuși (prompturi, scripts, arhitectură, SKILL.md). Well-tested, gate-validated.
2. **`--on-code` (EXPERIMENTAL_DRAFT):** auditează decizii pe cod user (PR-uri, refactor-uri, decizii arhitecturale) prin `prompts/lenses/domain_lens.md#code_domain`. Orchestratorul TREBUIE să pre-computeze `diff`, `files_touched`, `success_criterion`, `magnitude`, `reversibility`, `blast_radius` înainte de dispatch (vezi `scripts/dispatch_senate_on_code.py`). NOT wired în dispatch table până empirical gate met (vezi Drafts footnote la finalul Senate mode section).

**Mecanica:** 7 sub-agenți Sonnet 4.6 într-o primă rundă paralel + (opțional) cross-questions multi-round, fiecare cu prompt-ul lui din `prompts/senators/`:

| Senator | Specialitate |
|---|---|
| Wittgenstein | termeni vagi, definiții testabile |
| Aurelius | reversibility × magnitude, proporționalitate cost/stake |
| Confucius | autoritate, precedente în `runs/` + `experiments/` |
| Socrate | premize load-bearing nedeclarate |
| Musk | aggressive deletion + 10% add-back |
| Dimon | stress test, counterparty, silent failure modes |
| Napoleon | tokens, ore, starea operatorului |

**Cost:** 7 sub-agenți Sonnet (~2.3× Parallel). On-demand only — niciun trigger automat.

### Operational definitions

Pentru a putea verifica că Senatul a rulat corect, doi termeni-cheie au definiții testabile:

- **"Senate run end-to-end"** = (a) bundle `runs/senate/<timestamp>-<label>.json` există pe disc; (b) parsabil JSON; (c) conține `verdict ∈ {GO, MODIFY, STOP, DEEPLY_SPLIT, UNREACHABLE}` și `vote_counts`; (d) `senate_synth.py` exit 0.
- **"Senate nu atinge voci/moduri existente"** = `git diff <base>..HEAD -- prompts/{generator,control,conservator,skeptic,generator_pass2,control_pass2,conservator_pass2,*_lens}.md scripts/{aggregator,confidence,dialectic_merge,validate_report,build_report,personalities,strip_context,priors}.py` returnează empty. Adăugiri la SKILL.md Resources table sau secțiuni noi sunt explicit permise.

### Când să folosești

- Modificări la `prompts/*.md` core sau la Constitution/Workflow din SKILL.md
- Voci/moduri noi înainte să implementezi
- Decizii arhitecturale ireversibile (schemă `runs/*.json`, semantica veto-urilor)
- Self-improvement loop pe propriile schimbări (versiune mai puternică decât `/consilium parallel`)

### Workflow

1. **Formulează propunerea concret** — paragraf: ce schimbi, de ce, fișiere atinse, success criterion.
2. **Dispatch 7 sub-agenți paralel** (model default per `## Dispatch defaults`), fiecare cu prompt-ul senatorului inline. Input identic:
   ```
   Proposal under audit: <textul>
   Context: <fișiere atinse, success criterion>

   Your role and instructions:
   <conținutul prompts/senators/<senator>.md>

   Return STRICTLY the JSON specified in the "Output format" section. No prose.
   ```
3. **Retry 1× pe senator absent / JSON malformat.** La eșec, marchează `absent` și continuă.
4. **Cross-questions (Law 2 — opțional, multi-round).** Scanează output-urile Round 1 pentru `cross_questions[]`. Pentru fiecare `{to: <senator>, question: ...}`, dispatch focal pe senatorul-țintă cu input "Round 1 ai votat X. Senator Y te întreabă: <question>. Răspunde cu output complet actualizat — votul poate fi diferit." Counter per senator per rundă (max 3 — Law 2). Maximum 3 runde total. Dacă Round 2 ridică noi cross-Qs, repetă în Round 3 apoi STOP forțat.
5. **Blocaj resolution (Law 3 — opțional).** Dacă după Round 3 încă există 2 senatori în GO×STOP opposition (synthesizer raportează `blocaj_pending`), dispatch ceilalți 5 cu argumentele ambelor părți și întreabă care e mai puternic. Strânge `votes_from_others: {<senator>: <pair_member>}` și dă orchestrator-ului blocaj_resolution în input-ul de synth.
6. **Rulează synthesizer:** `cat senate_input.json | python -X utf8 scripts/senate_synth.py`
   - **Input format (multi-round):** `{"proposal": "...", "label": "...", "rounds": [{"round": 1, "senators": {...}}, ...], "blocaj_resolution": {...}, "absent": [...]}` — vezi docstring.
7. **Bundle salvat automat** în `runs/senate/<YYYY-MM-DD_HHMMSS>-<label>.json` (granularitate secunde + suffix `_v2/_v3...` pe coliziune — niciun overwrite tăcut). Bundle include `rounds`, `position_changes`, `cross_questions_used`, și (dacă aplicat) `blocaj_resolution` + `vote_counts_pre_blocaj`.
8. **Verdictul e advisory** — user-ul decide:
   - `GO` (≥7/9 GO **și** MODIFY==0) → procedezi
   - `STOP` (≥7/9 STOP **și** MODIFY==0) → propunerea e blocată; revizuie sau override explicit
   - `MODIFY` (orice vot MODIFY > 0) → propunerea trebuie revizuită înainte să poată atinge GO/STOP. Două căi: **accept** (tratează `modify_requests` ca TODO advisory) sau **R2** (re-rulează Senate cu propunere revizuită care adresează `modify_requests`-urile). Dacă R2 produce MODIFY 3 cicluri consecutive, avertisment soft: "consideră accept sau descompune propunerea."
   - `DEEPLY_SPLIT` (nici GO nici STOP nu ating QUORUM=7, MODIFY==0) → advisory: orchestratorul escaladează la user cu vote matrix. User poate forța senatorii cu ABSTAIN să declare o poziție (GO sau STOP) și/sau să override manual.
   - `UNREACHABLE` (voturi active < `MIN_ACTIVE_VOTES=5` — prea puțini senatori au luat o poziție) → orchestratorul prezintă user-ului două opțiuni:
     1. **Forțează senatorii ABSTAIN** să declare GO sau STOP și re-rulează Senate
     2. **Rulează Consilium normal** (mod sequential/dialectic/trias) pe aceeași propunere — senatul e înlocuit cu deliberarea standard

### ABSTAIN și MIN_ACTIVE_VOTES

`ABSTAIN` = prezent-fără-poziție. Nu reduce `voters_present`, nu intră în tally. Dacă ≥3/9 senatori abstain, warning `high_abstain_rate`.

`MIN_ACTIVE_VOTES=5`: dacă mai puțin de 5 senatori au votat activ (GO/MODIFY/STOP), verdictul e `UNREACHABLE` indiferent de distribuție — deliberarea e insuficient reprezentată. La `DEEPLY_SPLIT` (active ≥ 5 dar nici GO nici STOP nu ating QUORUM=7 și MODIFY==0), user-ul poate forța senatorii ABSTAIN să aleagă o tabără și re-rula.

### Routing boundary (EXPERIMENTAL — when to choose senate vs other modes)

| Decision profile | Mode |
|---|---|
| `reversibility=irreversible` OR `magnitude=critical` AND change spans ≥2 architectural layers | `senate --on-code` (*) |
| `confidence ∈ [0.5, 0.7]` from standard mode AND single drift concern | `dialectic + skeptic_on_chosen` |
| 2+ plausible architectural approaches without clear winner | `trias` |
| Bugfix evident OR diff <20 lines / 1 fișier | Sequential (scope_gate skips) |
| All other PR-level reviews | Sequential / Parallel auto cross-check |

> **(*) Pre-gate caveat — EXPERIMENTAL_DRAFT phase only.** `senate --on-code` routing applies ONLY to pilot dispatches explicitly designated for gate evidence. During the empirical gate phase (≥3 pilot runs required), production critical/irreversible decisions MUST be routed to `trias` or `dialectic + skeptic_on_chosen` (gate-validated modes). Pilots intentionally target the high-stakes profile for falsification evidence but are NOT a substitute for production audits until gate criteria met (≥7/10 info-add over Trias AND `semantic_suspect` ≤20%). This caveat is removed from SKILL.md upon successful gate promotion.

### Drafts footnote — EXPERIMENTAL_DRAFT modes

- **`senate --on-code`** (status: EXPERIMENTAL_DRAFT). Lens: `prompts/lenses/domain_lens.md#code_domain`. Gate criteria: ≥3 pilot runs with ≥2/3 info-add over Trias (measured via `scripts/compare_senate_vs_trias.py`) AND `semantic_suspect` ≤20% per run. If gate fails after 5 pilots → marked DEPRECATED_DRAFT, `runs/senate/` pilot bundles preserved as forensic evidence. **Do not depend on this mode for critical merge decisions until gate met.**

### Skip Senate dacă

- Schimbarea e pe deliberare standard, nu pe skill, ȘI nu satisface criteriile routing boundary pentru `--on-code` → folosește `parallel` / `dialectic` / etc.
- Schimbarea e trivial-textuală (typo, rename intern, fix doc) — cost-prohibitive
- User declină explicit

### Senator context injection (Pilot B)

**Status: pilot — zero code, orchestrator-only behavior.**

La Step 2 (dispatch), înainte de a trimite input-ul fiecărui senator, orchestratorul poate prepend un bloc de context din rulările senate anterioare:

```
Past votes for <senator_name> (inject only if N≥5 senate runs with recorded outcome):
- <label> | <vote> | <outcome>   # most recent
- <label> | <vote> | <outcome>
- <label> | <vote> | <outcome>   # oldest of 3
```

**Reguli operaționale:**
- Schema injectată: `{label, vote, outcome}` triples, N=3 cele mai recente, ordonate descendent după timestamp
- Sursa: `runs/senate/*.json` — citit manual de orchestrator (nu există script automat în Pilot B)
- **Activation gate:** nu injecta dacă `runs/senate/` are sub 5 rulări cu outcome confirmat (OK/BAD) în `FEEDBACK.html`. Sub acest prag, datele sunt prea sparse pentru a fi semnal.
- **Filtrează PEND:** injectează doar rulări cu outcome OK sau BAD — PEND înseamnă verdict neconfirmat
- **Falsification signal:** Pilot B produce semnal măsurabil dacă `modify_request`-ul unui senator referențiază explicit un label sau outcome din contextul injectat. Fără acest semnal după 5 rulări, Pilot B nu a adăugat valoare.
- **Reversibilitate completă:** oprești injectarea → comportament identic cu A (do_nothing)

**Escalare la C:** dacă după 5 rulări sub Pilot B cel puțin 1 senator referențiază context injectat, implementează `priors.py --senator <name>`:
- Flag adaugă filtrare per senator peste logica existentă (~50-60 linii)
- Trebuie să gestioneze schema multi-round `{rounds: [...]}`
- Injectează votul din ultima rundă (nu round 1)
- `priors.py` fără `--senator` returnează output identic cu azi (backward compat garantat)
- D (per_senator_json, 7 fișiere + update script) rămâne off-table până Napoleon's gate: ≥20 rulări senate, ≥80% outcome tracking

### Smoke test

Două nivele:
```bash
cat scripts/senate_synth_fixture.json | python -X utf8 scripts/senate_synth.py   # fixture quick check
python -X utf8 scripts/test_senate_synth.py                                       # 9-test suite
```
Suita rulează: prompt structure, fixture, verdict GO unanimous/GO supermajority (7/9), MODIFY-blocks, UNREACHABLE (sub MIN_ACTIVE=5), unrecognized-vote, **multi-round position change (Law 2+4)**, **cross-questions violation (Law 2)**, **blocaj pending + blocaj resolution (Law 3)**, DEEPLY_SPLIT (sub-QUORUM splits), ABSTAIN voters_present + MIN_ACTIVE boundary, bundle persistence, collision-safe write. Toate 20 trebuie PASS înainte de commit pe `senate_synth.py` sau orice `prompts/senators/*.md`.

### Origine + arhitectură

- **Arhitectură vizuală:** [`docs/architecture.html`](docs/architecture.html) — tab **Senate** (dark theme; cei 7 senatori cu specialități + flow dispatch + verdict logic + cross-questions matrix + blocaj resolution + cele 5 Legi + file map).
- **Justification empirică:** `experiments/New phase senat/deliberations/RUND2-deliberari.md`. Post PR `feat/senate-laws-2-3-4`, Laws 2-4 sunt opt-in multi-round; format multi-round `{rounds: [...]}` este singurul suportat.

<!-- === RUND2 === -->
## Three-layer architecture (RUND2)

| Layer | Components | Role |
|---|---|---|
| **Deliberation** | Conservator → Generator → Control (sequential) | Runs on every user question |
| **Aggregation** | aggregate_rund2() with 8-component veto cascade | Synthesizes voice outputs, decides what user sees |
| **Senate** | 7 senators (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon) | On-demand audit of proposed changes to consilium itself |

## Sequential dispatch (RUND2)

Default order: **Conservator → Generator → Control**

`strip_context.py` applies ONLY in Sequential mode (Steps 3-4) — Parallel dispatches sub-agents in isolation and does not use it.

1. Conservator sets `tokens_budget` and `irreversibility_flag`
2. Generator receives `magnitude`, `counterparty_risks`, `tokens_budget.generator` (NOT `meta_recommendation`)
3. Control receives full outputs from both Conservator and Generator

**Role separation, not Chinese wall.** Sequential runs the same LLM playing three roles in the same context window; `strip_context.py` strips the prior voice's prompt, but does not clear the model's in-context memory. This is a known, deliberate limitation — role prompts provide separation, not true isolation. True isolation requires Parallel sub-agents.

Auto-parallel cross-check: triggered only when Conservator outputs `magnitude: critical` AND `reversibility: irreversible`. Not user-selectable.

Silent audit: every 20 runs, parallel mode runs silently alongside sequential. If systematic divergence detected → audit frequency increases to 1/5.

## Veto powers (RUND2)

The 8 design components (per spec): vocabulary_map, length_targets, priority_veto_order, tension_expose, metadata, user_profile, multi_confidence, escalation_rule. The `aggregate_rund2()` function produces 7 distinct routing outcomes derived from these components: `BLOCK` (glossary_fail), `BLOCK` (irreversibility), `REWORK`, `ADAPT_SHORT`, `ADAPT_EXTENDED`, `ESCALATE` (3+ triggers), `AGGREGATE` (default).

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `irreversibility_flag: true` | Conservator | BLOCK (hard) | Ask user for explicit consent before Generator |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | ADAPT_SHORT | Short path: max 2 candidates, 2-sentence output |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |

Veto budget for `meta_recommendation`: 5 activations of `scale_up` or `scale_down` per month. On exhaustion → soft warning only, not blocking.

<!-- === END RUND2 === -->
