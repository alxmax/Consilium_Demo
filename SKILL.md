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
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite scripturi deterministe |
| `scripts/usage.py` | Rollup telemetry din runs/ |
| `agents/consilium-subagent.md` | Subagent pentru invocare izolată via `Agent(subagent_type="consilium-subagent", ...)` |

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

**Default-ul e parallel.** Dispatch cele 3 voci ca sub-agenți independenți — elimină cross-contamination complet.

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
