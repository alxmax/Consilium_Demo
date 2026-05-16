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
2. **Rulează `python scripts/priors.py`** — întoarce priori soft din `FEEDBACK.html` + `runs/`. Trei câmpuri ne pot bloca deliberarea curentă până sunt rezolvate:
   - `stale_pendings` non-empty (PEND mai vechi de 2 zile): întreabă *"Ai N entries PEND vechi: [date | chosen] × N. Vrei să le închid (OK/BAD/skip)?"* — actualizează cu `mark_outcome.py --date <d> --chosen <id> --outcome OK|BAD` (preferat) sau cu `Edit` direct pe `FEEDBACK.html`. **Nu** folosi `log_feedback.py` — duplichează rândul.
   - `missing_feedback_runs` non-empty: rulează `python scripts/audit_feedback.py --backfill` ca să creezi PEND-uri pentru runs orfane, apoi rezolvă-le ca mai sus. Dacă lista e mai mare de 3, prefer să rezolvi gap-ul *înainte* de a începe o deliberare nouă.
   - `pend_pressure > 0.3` (raportul PEND în ultimele N=20 entries — pragul a scăzut de la 0.5): alertă soft *"{pend_count}/{window_size} entries recente sunt PEND — consideri să le închizi?"* — nu bloca, dar înregistrează semnalul.

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

### 2. Conservator — assess risc (runs FIRST)
Folosește `prompts/conservator.md`. Rulează **înainte** de Generator și Control. Output-ul setează `tokens_budget` pentru celelalte voci.

Required Questions (Q1-Q5): reversibility, magnitude, counterparty_risks, status quo bias check, meta_recommendation.

Output per candidate: `{id, regression_risk: {reversibility, magnitude, net_concern}, counterparty_risks, bias_check, meta_recommendation, tokens_budget: {generator, control}, irreversibility_flag, rollback_recipe, notes}`.

**Sequential-first.** Conservator runs before Generator and Control. Its `tokens_budget` output caps how deep the other voices go. Its `irreversibility_flag: true` BLOCKS the pipeline — confirm user consent before proceeding.

**Veto check (auto, after Conservator output):**
- If `irreversibility_flag: true` → stop, ask user: *"Conservator marcheaza aceasta decizie ca ireversibila. Confirmi ca vrei sa continui?"* — proceed only with explicit YES.
- If `meta_recommendation: scale_down` → skip Generator's unconventional/adversarial candidates; cap at 2 candidates; use short path.
- If `meta_recommendation: scale_up` → warn user, add context request before Generator.

**Opțional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Ancorează `magnitude` la `files_changed/lines_*` și `regression_risk.net_concern` la distribuția de churn când prezent.

### 3. Generator — produce alternative
Folosește `prompts/generator.md`. Cere **3–5 candidate**, inclusiv `do_nothing`. Stil divergent. Respectă `tokens_budget.generator` setat de Conservator.

Output: `{candidates: [{id, summary, sketch, rationale, downside_estimate}], fallback_scenario, coverage_check, challenge_upward, abstain, preferred}`. Adversarial e condiționat (clarity gate a returnat 2+ interpretări SAU schimbarea atinge shared/core code) — altfel emit `"adversarial_skipped": "<reason>"`.

**Receives from Conservator (selective):** `magnitude`, `counterparty_risks`, `tokens_budget.generator`. Does NOT receive `meta_recommendation` — that is policy, not Generator input.

**Challenge upward:** If Generator sets `challenge_upward.triggered: true`, re-run Conservator with Generator's context before proceeding to Control.

### 4. Control — verifică corectitudine
Folosește `prompts/control.md`. Per candidate: types, logică, tests, style.

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

**Acțiuni finale (obligatorii — deliberarea nu e completă fără ele):**

Cele două apeluri de mai jos sunt **obligatorii**. Dacă orchestratorul oprește înainte de a le rula, raportul există pe disc dar e invizibil pentru priors → următoarea deliberare nu va beneficia de feedback-ul ăsta. Audit periodic: `python scripts/audit_feedback.py` listează runs orfane; cu `--backfill` adaugă rânduri PEND default.

1. **Persistă raportul** în `runs/YYYY-MM-DD_HHMM_<label>.json`.
2. **Loghează în `FEEDBACK.html`** (confidence-gated, fără să sări vreun caz):
   - `confidence >= 0.7` → `python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/<file>.json < runs/<file>.json`
   - `confidence < 0.7` → întreabă: *"Confidence sub prag (`<X>`). Vrei să override-ezi `<chosen>`? Alternative: `<alt_ids>`. Răspunde alt_id, 'no', sau 'skip'."* Apoi: `no` → `--outcome OK --force-override`; `<alt_id>` → `--outcome OVR --override-target <alt_id>`; `skip` → fără flag (PEND, dar **nu lăsa apelul să fie sărit**).
   - `confidence null` (toți vetoiți) → `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json`

**Outcome confirmation (retroactiv).** Outcome-ul logat la pasul 2 e subiectiv — reflectă impresia imediată. Dacă mai târziu producția dezvăluie un regression sau o alegere bună, suprascrie-l cu marker confirmat:
```bash
python scripts/mark_outcome.py --run-path runs/<file>.json --outcome BAD --reason "broke prod migration"
```
Marker-ul `[confirmed]` apare în note; `priors.py` ponderează aceste rânduri 2x față de feedback-ul subiectiv (vezi `weighted_bad_rate`).

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
| `scripts/audit_feedback.py` | Listează runs fără rând FB; cu `--backfill` adaugă PEND default |
| `scripts/memory.py` | Read API uniform peste cele 3 tiers (short/medium/long) |
| `scripts/strip_context.py` | Proiectează output voce anterioară la minim (Steps 3-4 sequential) |
| `scripts/dialectic_merge.py` | Combină Pass-1 + Pass-2 în payload aggregator-ready |
| `scripts/personalities.py` | Trias mode — 3 personalități fixe cu weights + lens paths |
| `prompts/skeptic.md` | Voce focală pentru `parallel_skeptic` și `dialectic_skeptic` — primește doar chosen, produce obiecție concretă sau `meta_scope_mismatch` |
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite scripturi deterministe |
| `scripts/usage.py` | Rollup telemetry din runs/ |
| `agents/consilium-subagent.md` | Subagent pentru invocare izolată via `Agent(subagent_type="consilium-subagent", ...)` |
| `prompts/senators/*.md` | 7 prompturi de audit pre-implementare (mod `senate`); fiecare cu specialitate distinctă (vezi tabelul din Senate mode) |
| `scripts/vocabulary_map.py` | RUND2: traduceri user-facing (reversibility/magnitude/meta_recommendation/verdict) + `compute_tokens_budget(magnitude, reversibility, meta)` |
| `scripts/principle_extraction.py` | RUND2 EXPERIMENTAL, INACTIVE — extract principles din `runs/` dacă coverage ≥ 80% și ≥ 10 entries pe categorie verificabilă |
| `scripts/senate_synth.py` | Synthesizer Senate: agregă 7 output-uri JSON → verdict GO/MODIFY/STOP + modify_requests + risks → salvează în `runs/senate/`. Suportă **multi-round (Laws 2-4)** via schema `{rounds: [...]}` cu `cross_questions[]`, `position_changes[]`, și `blocaj_resolution` (5-vote tiebreaker). Backward compat pe legacy `{senators: {...}}`. |

## Feedback loop

- **`runs/`** — JSON per deliberare în `runs/YYYY-MM-DD_HHMM_<label>.json` (schema în `runs/README.md`). Gitignored. Citit de `priors.py` (Step 0), `usage.py`, `feedback.py`.
- **`FEEDBACK.html`** — o linie per folosire: `data | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. Local, gitignored. **Drill-down:** când `log_feedback.py` appendează, rows existente pierd drill-down-ul; folosește `migrate_feedback_md_to_html.py` pentru re-populare în bulk.
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

## Dialectic mode (opt-in, two-pass)

Two-pass: Pass 1 = parallel; Pass 2 = fiecare voce revizuiește văzând output-urile celorlalte două. Cost: 2× parallel. Implementat în `scripts/dialectic_merge.py`.

**Pass-2 schema (obligatorie per item).** Fiecare item Pass-2 (candidate / verdict / score) trebuie să emită fie `revision: <noul conținut>` fie `maintained: <motiv>`. Lipsa ambelor → `dialectic_merge.py` îl tratează ca dissent fallback și emite stderr warning (`[warning] dialectic pass-2 dissent fallback for <voice>: <ids>`). Candidate Pass-1 omise complet din Pass-2 generator declanșează `silently_dropped` warning și sunt recuperate din Pass-1.

Audit warnings la stderr după merge — verifică-le înainte să consideri 2× cost-ul justificat.

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
| 2-1 | 0.70 | OK auto |
| 2-0 | 0.75 | OK auto |
| 1-1-1 / 1-1-0 / 1-0-0 | null | PEND |
| 0-0-0 | null | PEND + retry_suggested |

### Failure recovery
- **1-1-1 fragmentation:** orchestrator întreabă user — accept one, re-run with constraints, or abort
- **0-0-0 total veto:** emite `retry_suggested` cu relaxed threshold sau Generator constraints

### Skip Trias dacă
- Diff < 20 lines / 1 fișier — `scope_gate.py` va skip oricum
- Conservatism strict cerut (Trias agregat e −18% Conservator)
- Bugfix evident — Sequential blind ajunge

## Parallel + Skeptic mode (`parallel_skeptic`)

**Mecanica:** Parallel standard (3 voci Sonnet) + 1 voce **Skeptic** focală care primește DOAR chosen-ul (nu și ceilalți candidați, nu și verdicts-urile). Skeptic-ul produce o obiecție concretă pe chosen sau marchează `meta_scope_mismatch` dacă deliberarea însăși e supra-aplicată.

**Cost:** 4 sub-agenți (1.33× Parallel).

### Când să folosești
- Confidence-ul din Parallel cade în banda `[0.5, 0.7]` — nu suficient pentru ship, nu suficient de jos pentru retry
- Schimbări medium-stakes unde vrei un challenge focal post-hoc fără cost Trias
- Probleme unde over-engineering e un risc real (trivial-but-framed-as-complex)

### Workflow
1. Rulează Parallel normal (Gen/Ctrl/Cons în paralel pe Sonnet 4.6) → produce `chosen` + `confidence`
2. Dacă `confidence ∈ [0.5, 0.7]`, dispatch 1 sub-agent Sonnet 4.6 cu `prompts/skeptic.md` inline + input minim:
   ```
   chosen: <id, summary, sketch, rationale>
   success_criterion: <propoziția testabilă>
   verification: <comanda>
   ```
   NU pasezi alte candidate sau scoruri.
3. Validează skeptic output-ul:
   - `can_object: true` cu `concrete_concerns` ≥ 2 SAU `quoted_scenario` non-null → accept
   - `can_object: true` fără evidence → reject (schema fail), ship chosen original
   - `can_object: false` → ship chosen original, conf upgrade
4. Acțiune pe baza `addressable`:
   - `in_place` → ship chosen cu nota din skeptic în `deliberation_log`
   - `requires_redesign` → ask user: alternative din `alternatives`?
   - `unaddressable` cu `failure_mode: meta_scope_mismatch` → marchează raportul `misapplied`, log în FEEDBACK ca outcome=PEND cu nota "scope mismatch"

### Skip parallel_skeptic dacă
- Confidence ≥ 0.7 — skeptic n-are ce găsi
- Confidence < 0.5 — prea jos, escaladare directă la Trias sau user
- Diff e high-stakes intrinsec (auth, migrations) — folosește Trias direct

## Dialectic + Skeptic mode (`dialectic_skeptic`)

**Mecanica:** Dialectic two-pass standard (6 voci Sonnet) + 1 voce **Skeptic** focală pe chosen-ul final (același prompt și schema ca la `parallel_skeptic`). Skeptic-ul rulează după Pass 2, post-aggregation.

**Cost:** 7 sub-agenți (~2.3× Parallel).

### Când să folosești
- Schimbări cu trade-off-uri reale care beneficiază de cross-review (Dialectic) PLUS un challenge focal final
- Decizii medium-stakes unde vrei și revizia inter-voci (Dialectic catches some errors during Pass 2) ȘI o ultimă verificare focală
- NU pentru detectarea fabricațiilor introduse în Pass 2 — Dialectic Pass 2 e sursa fabricațiilor cunoscute (vezi `experiments/run2-p3-reruns.html`), iar skeptic-ul vine după și nu poate unwind drift-ul Pass 1 → Pass 2

### Workflow
1. Rulează Dialectic complet (`scripts/dialectic_merge.py`) → `chosen` din Pass 2
2. Dispatch skeptic cu același prompt minimal ca la `parallel_skeptic`
3. Validare + acțiune identică cu `parallel_skeptic`

### Limitare cunoscută
Skeptic-ul vede DOAR chosen final, nu și Pass 1 vs Pass 2 drift. Dacă Dialectic Pass 2 fabricat constraint care a deplasat chosen, skeptic-ul evaluează doar finalitatea, nu mișcarea. Pentru drift detection, e nevoie de un mod separat (planificat: `dialectic_drift_guard`).

## Trias split-model mode (`trias_split`)

**Mecanica:** Trias standard (3 personalități × 3 voci = 9 sub-agenți) cu override de model:
- **Generator voices** (1 per personalitate, 3 total) → Sonnet 4.6 (creativitate)
- **Control + Conservator voices** (2 per personalitate, 6 total) → Haiku 4.5 (verificare rapidă)

**Cost:** ~3.3× Parallel (vs 9× Parallel pentru Trias full).

### Când să folosești
- Decizii medium-stakes care beneficiază de diversitatea de personalități (3 perspective ortogonale) dar nu justifică costul Trias full
- Probleme unde verificarea e relativ surface-level (factor scoring, sanity checks) — Haiku ajunge
- Haiku verifiers: efect anti-zgomot pe probleme triviale fără constraint implicit (resping elaborări inutile), dar shallow-amplifier pe probleme cu constraint implicit — confirmă răspunsul evident fără să interogheze asumpția ascunsă (P3 corrigendum: 3/3 A pe o problemă cu răspuns corect C; vezi `experiments/p3-car-wash.html`). Nu folosi trias_split dacă problema poate conține constraints implicite — preferă Trias full sau `parallel_skeptic`.

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

**Mecanica:** `skeptic_on_chosen` este un **flag cross-cutting**, nu un mod fix. Se compune peste orice mod de bază (Sequential, Parallel, Dialectic, Trias): după ce modul de bază produce `chosen` și `confidence`, se dispatch-uiește 1 voce Skeptic suplimentară pe `chosen`-ul rezultat, cu același prompt `prompts/skeptic.md` și același input minimal ca în `parallel_skeptic`. Diferența față de modurile cu Skeptic baked-in: flagul rulează **secvențial post-hoc** pe orice mod, nu în paralel cu Pass-1. Nu există cod Python dedicat — orchestrarea se face prin dispatch standard al `prompts/skeptic.md` cu chosen-ul curent, identic cu Step 2 din `parallel_skeptic`.

**Cost:** +1 sub-agent față de modul de bază ales (indiferent care e acela).

**vs `parallel_skeptic`:** aceea e un mod fix (Parallel + Skeptic simultan, 4 sub-agenți); `skeptic_on_chosen` e flag composabil pe orice mod.
**vs `dialectic_skeptic`:** aceea e un mod fix (Dialectic + Skeptic post-Pass-2, 7 sub-agenți); `skeptic_on_chosen` e echivalentul generalizat care produce același efect și pe Sequential / Parallel / Trias.

### Când să folosești
- Confidence-ul din modul de bază cade în banda `[0.5, 0.7]` — trigger **automat** (același prag ca `parallel_skeptic`; aggregator-ul poate semnala banda, orchestratorul aplică flagul)
- **Opt-in manual** via `--skeptic-on-chosen` când vrei un challenger focal post-hoc indiferent de confidence (medium-stakes, probleme cu constraint-uri implicite cunoscute)
- Probleme unde chosen_confirmation_pass a demonstrat valoare empirică — în special situații cu constraint-uri implicite nemenționate explicit în success_criterion (tip P3: precondițiile logice ale soluției nu apar în enunț)
- Când baza e Sequential sau Trias și vrei challengerul focal fără a rula un întreg `parallel_skeptic` sau `dialectic_skeptic`
- Cazuri unde vrei să știi dacă chosen a ratat ceva, dar nu ai o bază de comparație (nu ai alternative viabile) — Skeptic-ul focal pe chosen e mai ieftin decât re-rularea întregii deliberări

### Workflow
1. Rulează modul de bază complet (oricare: Sequential / Parallel / Dialectic / Trias) → produce `chosen`, `confidence`, raport intermediar
2. Dacă `confidence ∈ [0.5, 0.7]` (auto) sau flagul `--skeptic-on-chosen` e activ, dispatch 1 sub-agent Sonnet 4.6 cu `prompts/skeptic.md` inline + input minimal:
   ```
   chosen: <id, summary, sketch, rationale>
   success_criterion: <propoziția testabilă>
   verification: <comanda>
   ```
   NU pasezi alte candidate, scoruri sau log-uri de deliberare.
3. Validează skeptic output-ul (identic cu Step 3 din `parallel_skeptic`):
   - `can_object: true` cu `concrete_concerns` ≥ 2 SAU `quoted_scenario` non-null → accept
   - `can_object: true` fără evidence → reject (schema fail), ship chosen original
   - `can_object: false` → ship chosen original, loghează că nu există obiecție concretă
4. Loghează rezultatul în `deliberation_log` cu step `"skeptic_on_chosen"` și setează flag `skeptic_caught_constraint: true|false` în raport
5. Aplică override semantics (secțiunea de mai jos)

### Override semantics
**Advisory by default.** Verdictul Skeptic-ului se loghează în `deliberation_log` ca entry cu step `"skeptic_on_chosen"` și flag `skeptic_caught_constraint: true|false`. `chosen` **nu se înlocuiește** — rămâne cel produs de modul de bază. Utilizatorul vede obiecția în raport și poate acționa sau ignora.

**Opt-in override via `--skeptic-can-override`.** Dacă flagul e activ ȘI Skeptic produce `addressable: requires_redesign`, verdictul Skeptic-ului supersedează `chosen`: orchestratorul prezintă utilizatorului alternativele din raport și întreabă dacă vrea să schimbe alegerea. Dacă Skeptic produce `addressable: in_place`, override-ul nu se aplică (advisory rămâne); dacă produce `addressable: unaddressable` cu `failure_mode: meta_scope_mismatch`, raportul e marcat `misapplied` (identic cu `parallel_skeptic`).

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
- Baza e deja `parallel_skeptic` sau `dialectic_skeptic` — Skeptic-ul e deja inclus în acele moduri, a doua rulare ar fi redundantă
- Diff e high-stakes intrinsec (auth, migrations, security) — folosește Trias full cu cost justificat

**Origine empirică.** Modul a apărut din analiza `experiments/p3-car-wash.html`: `chosen_confirmation_pass` (echivalentul conceptual al acestui flag) a atins catch-rate 100% în simulare și 4/7 în reruns reale pe P3 car wash — performanță superioară oricărui alt mod testat. Mecanismul: o singură voce skeptic pe `chosen` post-hoc obligă re-citirea success_criterion și detectarea constraint-urilor implicite ratate de toate vocile din Pass-1.

## Senate mode (`senate`)

**Scope distinct:** `senate` auditează **modificări la skill-ul însuși** (prompturi, scripts, arhitectură, SKILL.md), nu întrebări ale user-ului. Pentru cod user folosești modurile standard.

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

- **"Senate run end-to-end"** = (a) bundle `runs/senate/<timestamp>-<label>.json` există pe disc; (b) parsabil JSON; (c) conține `verdict ∈ {GO, MODIFY, STOP, UNREACHABLE}` și `vote_counts`; (d) `senate_synth.py` exit 0.
- **"Senate nu atinge voci/moduri existente"** = `git diff <base>..HEAD -- prompts/{generator,control,conservator,skeptic,generator_pass2,control_pass2,conservator_pass2,*_lens}.md scripts/{aggregator,confidence,dialectic_merge,validate_report,build_report,personalities,strip_context,priors}.py` returnează empty. Adăugiri la SKILL.md Resources table sau secțiuni noi sunt explicit permise.

### Când să folosești

- Modificări la `prompts/*.md` core sau la Constitution/Workflow din SKILL.md
- Voci/moduri noi înainte să implementezi
- Decizii arhitecturale ireversibile (schemă `runs/*.json`, semantica veto-urilor)
- Self-improvement loop pe propriile schimbări (versiune mai puternică decât `/consilium parallel`)

### Workflow

1. **Formulează propunerea concret** — paragraf: ce schimbi, de ce, fișiere atinse, success criterion.
2. **Dispatch 7 sub-agenți paralel** (`model: "sonnet"` explicit), fiecare cu prompt-ul senatorului inline. Input identic:
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
   - **Legacy:** `{"proposal": "...", "label": "...", "senators": {...}, "absent": [...]}` (single-round; Laws 2-4 inactive)
   - **Multi-round (Laws 2-4):** `{"proposal": "...", "label": "...", "rounds": [{"round": 1, "senators": {...}}, ...], "blocaj_resolution": {...}, "absent": [...]}` — vezi docstring.
7. **Bundle salvat automat** în `runs/senate/<YYYY-MM-DD_HHMMSS>-<label>.json` (granularitate secunde + suffix `_v2/_v3...` pe coliziune — niciun overwrite tăcut). Multi-round bundle include `rounds`, `position_changes`, `cross_questions_used`, și (dacă aplicat) `blocaj_resolution` + `vote_counts_pre_blocaj`.
8. **Verdictul e advisory** — user-ul decide:
   - `GO` (≥5/7 GO) → procedezi
   - `STOP` (≥5/7 STOP) → revizuie propunerea sau override explicit
   - `MODIFY` (default) → aplică `modify_requests` și (opțional) re-rulează
   - `UNREACHABLE` (<5 senatori prezenți) → verdict structurally biased toward MODIFY; orchestrator escaladează la user

### Quorum sub absenți

`UNREACHABLE` apare când `voters_present < 5`. Sub acest prag, nici GO nici STOP nu pot fi atinse matematic, iar default-ul MODIFY ar fi înșelător. Synthesizer-ul emite warning explicit `quorum_unreachable` și verdict `UNREACHABLE` — orchestrator-ul trebuie să escaladeze.

### Skip Senate dacă

- Schimbarea e pe deliberare standard, nu pe skill → folosește `parallel` / `dialectic` / etc.
- Schimbarea e trivial-textuală (typo, rename intern, fix doc) — cost-prohibitive
- User declină explicit

### Smoke test

Două nivele:
```bash
cat scripts/senate_synth_fixture.json | python -X utf8 scripts/senate_synth.py   # fixture quick check
python -X utf8 scripts/test_senate_synth.py                                       # 9-test suite
```
Suita rulează: prompt structure, fixture, verdict GO unanimous/quorum, MODIFY default, UNREACHABLE, unrecognized-vote, **multi-round position change (Law 2+4)**, **cross-questions violation (Law 2)**, **blocaj pending + blocaj resolution (Law 3)**, **legacy backward compat**, bundle persistence, collision-safe write. Toate 14 trebuie PASS înainte de commit pe `senate_synth.py` sau orice `prompts/senators/*.md`.

### Origine + arhitectură

- **Arhitectură vizuală:** [`docs/senate/architecture.md`](docs/senate/architecture.md) (markdown) sau [`docs/senate/architecture.html`](docs/senate/architecture.html) (dark theme — vizualizări cross-questions matrix + blocaj resolution + flow runde).
- **Justification empirică:** `experiments/New phase senat/deliberations/RUND2-deliberari.md`. MVP curent = single-pass parallel; cross-questions + blocaj resolution documentate vizual în architecture.html §8 ca extensie viitoare (NU în MVP).

<!-- === RUND2 === -->
## Three-layer architecture (RUND2)

| Layer | Components | Role |
|---|---|---|
| **Deliberation** | Conservator → Generator → Control (sequential) | Runs on every user question |
| **Aggregation** | aggregate_rund2() with 8-component veto cascade | Synthesizes voice outputs, decides what user sees |
| **Senate** | 7 senators (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon) | On-demand audit of proposed changes to consilium itself |

## Sequential dispatch (RUND2)

Default order: **Conservator → Generator → Control**

1. Conservator sets `tokens_budget` and `irreversibility_flag`
2. Generator receives `magnitude`, `counterparty_risks`, `tokens_budget.generator` (NOT `meta_recommendation`)
3. Control receives full outputs from both Conservator and Generator

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

## Principle_Extraction (RUND2 — EXPERIMENTAL, inactive)

Script: `scripts/principle_extraction.py`

**Status: INACTIVE.** Blocked until:
1. `runs/` has >= 10 entries in target category
2. Outcome tracking active for >= 80% of runs
3. Category has externally-verifiable outcomes

**Supported categories (once active):** trading, code, real_estate

**Excluded categories (subjective):** career, relationships, mental_health

To activate: flip `_INACTIVE = False` in `scripts/principle_extraction.py` after verifying the 3 conditions. Once active, Conservator consults it before marking `magnitude`.
<!-- === END RUND2 === -->
