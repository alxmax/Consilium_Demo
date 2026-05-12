---
name: max-agent
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, or when uncertain between multiple implementation approaches.
---

# Max Agent — Code Deliberation Skill

Pattern de deliberare multi-perspectivă pentru orice modificare de cod. Trei voci independente colaborează pentru a evalua o schimbare:

- **Generator** (creativ) — propune alternative, divergent thinking
- **Control** (analitic) — verifică corectitudine tehnică
- **Conservator** (prudent) — evaluează risc și reversibilitate

## Constitution

Patru principii care guvernează **fiecare** deliberare. Au prioritate când o voce dă o recomandare ce intră în conflict cu ele.

1. **Think before coding.** Nu presupune. Nu ascunde confuzia. Expune tradeoff-urile explicit. Dacă requestul are 2 interpretări plauzibile, listează-le pe ambele ca `candidates` separate — nu alege tăcut.
2. **Simplicity first.** Minimum de cod care rezolvă problema. Refuză abstracții speculative, feature-uri nesolicitate, error handling pentru cazuri imposibile. `do_nothing` e în lista de candidați tocmai pentru asta.
3. **Surgical changes.** Atinge doar ce cere goal-ul. Fără refactor în zone adiacente "cât suntem aici". Conservator-ul măsoară asta prin factor-ul `scope_drift` — respectă un scor mare.
4. **Goal-driven execution.** Înainte de a genera candidate, restate goal-ul ca **success criterion** într-o singură propoziție testabilă. Output-ul final trebuie să includă un pas de **verification** ("cum știm că a funcționat").

*(Adaptat după CLAUDE.md al lui Andrej Karpathy, via [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).)*

## When to use

Activează acest skill când:
- Faci **review de PR** sau diff
- Planifici un **refactor** care atinge 2+ fișiere
- Trebuie să alegi între **mai multe abordări** de implementare
- Ești pe punctul de a face **commit pe cod shared/core**
- Vrei o **assessment de risc** înainte de a accepta o sugestie

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach".

## Workflow

### 0. Bootstrap (înainte de orice grep / Read pe codebase)
Două acțiuni, în ordine, **înainte** de a explora codul user-ului:

1. **Citește contractele celor 3 voci** — `prompts/generator.md`, `prompts/control.md`, `prompts/conservator.md`. Sunt scurte (sub 100 linii fiecare) și definesc exact ce câmpuri produce fiecare voce. Fără ele, gather-context-ul de la Step 1 rulează orb: framezi `success_criterion` într-un vocabular care s-ar putea să nu se mapeze pe `scope_drift` / `tests_to_write` / `rollback_recipe` etc. Cost: ~500 tokeni; previne re-explorare după ce ajungi la Step 3 și realizezi ce întreabă Control. **Notă pentru parallel/dialectic mode:** acolo conținutul fiecărui prompt trebuie *inline-uit* în dispatch-ul către sub-agentul respectiv (vezi secțiunea Parallel voices mode → "Conținutul integral al prompt-ului vocii sale"). Citirea la Step 0 nu e suficientă — sub-agenții n-au cum să acceseze fișierele.
2. **Rulează `python scripts/priors.py`.** Întoarce un JSON cu ultimele ~10 entries din `FEEDBACK.html`, `override_rate`, `bad_rate`, `conservator_veto_rate` (din `runs/`) și top keywords din note. Tratează ca **priori soft** pentru deliberarea curentă: dacă apar tipare clare (ex: `override_rate > 0.3` cu keyword "conservator", "agresiv"), ajustează strategia (ex: relaxează pragul veto la 0.8, marchează explicit unde Conservator e probabil supra-prudent). Nu modifica fișierele skill-ului; doar prompts-urile rămân autoritative.

   Dacă `priors.py` raportează `stale_pendings` non-empty (PEND-uri mai vechi de 7 zile, max 5 entries), oprește **înainte** de Step 1 și întreabă user-ul: *"Ai N entries PEND vechi: [date | chosen] × N. Vrei să le închid acum (OK/BAD/skip per entry) sau să continuăm cu deliberarea nouă?"* Update-ul se face cu `Edit` tool pe `FEEDBACK.html` (înlocuiește literalul `PEND` din linia respectivă cu `OK` sau `BAD`), **nu** prin `log_feedback.py` — acela appendează o linie nouă, ducând la istoric dublu pentru aceeași deliberare. Dacă user-ul răspunde "skip", continuă la Step 1 fără modificări.

### 1. Gather context & state the goal
Citește schimbarea propusă (diff, fișiere atinse). Identifică:
- Scope: câte fișiere, câte module, câte linii
- Tipul schimbării: bugfix, feature, refactor, cleanup
- Blast radius: cod intern, cod shared, API public

**Apoi formulează `success_criterion`** — o propoziție testabilă care descrie ce înseamnă "schimbarea a reușit". Acest criteriu condiționează toate candidate-urile de mai jos.

**Clarity gate.** Înainte de a continua la pasul 2, fă acest exercițiu mental: *poți tu, acum, scrie 2+ interpretări plauzibile distincte ale request-ului user-ului?* Dacă da, ești în zona de ambiguitate și Principle #1 e activ:

- **Stop.** Nu trece la Generator.
- Listează interpretările (2-4) într-un mesaj scurt user-ului.
- Întreabă explicit care e cea reală — sau dacă vrea ambele tratate ca candidate separate.

Semnale roșii care declanșează clarity gate:
- Verbe vagi ("fix", "improve", "clean up") fără obiect concret
- Pronume sau referințe nedezambiguate ("the bug", "this issue") când există mai multe candidate
- Scope implicit: user spune "refactor X" — vrea doar X sau și call sites?
- Unități/limite lipsă: "make it faster" fără benchmark sau prag

Dacă **toate** sunt clare → continuă la pasul 2 fără să întrebi. Clarity gate **nu** e o scuză să întrebi de rutină — întrebatul are cost. Folosește-l doar când interpretările diferă semnificativ în scope sau cod produs.

### 1.5. Scope gate (auto)
Înainte de Generator, rulează:
```bash
python scripts/scope_gate.py            # working tree vs HEAD
python scripts/scope_gate.py --ref main # main..HEAD
```
Întoarce `{should_skip, reason, signals, config_used}`. Dacă `should_skip: true`, deliberarea completă e overkill (cost-of-deliberation > stakes-of-change) — sari direct la raportul minimal de mai jos și oprește-te:

```json
{
  "success_criterion": "<din pasul 1>",
  "verification": "<pas concret>",
  "chosen_approach": "skipped",
  "skipped": true,
  "skip_reason": "<reason din scope_gate>",
  "signals": {"files_changed": 1, "lines_changed": 4, "blocklist_hits": []},
  "voice_scores": null,
  "confidence": null,
  "alternatives": [],
  "deliberation_log": []
}
```

Constitution Principle #4 rămâne — `success_criterion` și `verification` sunt obligatorii și pe raportul skipped (validate_report.py le verifică, plus `skip_reason` non-gol).

Defaults: `max_files=1`, `max_lines=15`, plus blocklist conservativ (`auth/`, `security/`, `migrations/`, `.github/workflows/`, `**/secrets*`, `.env*`, `Dockerfile`, `*.tf`, fișiere de dependențe). Scopul: o linie schimbată în `migrations/` nu sare gate-ul, oricât de mic e diff-ul. Override prin `scope_gate.json` în root cu schema `{max_files, max_lines, blocklist}` — vezi docstring-ul script-ului. Escape hatch: `MAX_AGENT_FORCE_FULL=1` în environment forțează `should_skip=false` indiferent de scope (când vrei deliberare oricum).

Gate-ul **eșuează deschis**: dacă probe-ul git crapă (no repo, bad ref), `should_skip: false` și treci la Generator. Mai bine deliberezi în plus decât sari în gol.

**Notă pentru task-uri non-diff** (audit de cod existent, architecture review, planning, design questions): scope_gate e un mecanism de cost-control specific pentru code-change pe un diff inspectabil. Când nu există diff (ex: "auditează folder-ul X", "ce abordare pentru feature Y?"), gate-ul fails open și e efectiv no-op — comportament intenționat, nu bug. Pentru aceste task-uri poți sări Step 1.5 explicit dacă vrei să eviți zgomotul în output.

### 2. Generator — produce alternative
Folosește `prompts/generator.md`. Cere **3–5 abordări candidate**, inclusiv "do nothing" ca baseline. Stil divergent — nu auto-cenzura pentru risc în acest pas.

Output per candidate: `{id, summary, sketch, rationale}`.

**Adversarial e conditional**, nu obligatoriu (vezi `prompts/generator.md` Constraints). Se include doar dacă (a) clarity gate-ul la Step 1 a întors 2+ interpretări plauzibile SAU (b) schimbarea atinge shared/core code. Altfel Generator emite `"adversarial_skipped": "<reason>"` și sare peste. Pentru task-uri trivial-bounded cu goal unambiguu, costul adversarial-ului depășește valoarea — skip-ul e by design.

### 3. Control — verifică corectitudine
Folosește `prompts/control.md`. Pentru fiecare candidate verifică:
- Types corect?
- Tests există / pot fi scrise?
- Logică validă (edge cases, error paths)?
- Style consistent cu codebase-ul?

Output per candidate: `{id, valid: bool, issues: [...], tests_to_write: [...]}`. `tests_to_write` e obligatoriu pentru candidate marcat `valid: true` (cu excepția `do_nothing`) — 1-4 teste de acceptanță cu `name` + `assert`.

**Sequential blind context.** Înainte de a apela Control în sequential mode, rulează:
```bash
cat generator_out.json | python scripts/strip_context.py --for control
```
Control primește doar `{id, summary, sketch}` per candidate — fără `rationale`. Asta reduce contaminarea: Control validează ce vede în sketch, nu se lasă convins de retorica Generator-ului. În parallel mode pasul nu e necesar (sub-agenții n-au cum să vadă unul output-ul celuilalt).

### 4. Conservator — assess risc
Folosește `prompts/conservator.md`. Pentru fiecare candidate **valid**, scorează:
- Diff size (linii atinse)
- Scope drift (atinge zone nelegate de task)
- Regression risk (probabilitate de a sparge ceva)
- Reversibilitate (cât de ușor revii dacă merge prost)

Output per candidate: `{id, risk_score: 0.0–1.0, factors: {...}, rollback_recipe: [...]}`. `rollback_recipe` e obligatoriu pentru orice candidate cu `risk_score >= 0.3` — 2-5 pași concreți (comenzi, acțiuni) pe care un on-call îi poate executa fără context suplimentar.

**Aggregation rule (din `prompts/conservator.md`, autoritar):** `risk_score` e media celor 4 factori, **cu o excepție** — dacă `reversibility > 0.7`, irreversibilitatea domină și `risk_score` nu poate cădea sub `reversibility`. Asta previne "diluarea" unui factor critic de către media celorlalți (un schema migration cu `reversibility=0.85` și ceilalți 3 factori la 0.1 nu trebuie să primească 0.29).

**Sequential blind context.** Înainte de a apela Conservator în sequential mode, rulează:
```bash
echo '{"candidates": [...], "verdicts": [...]}' | python scripts/strip_context.py --for conservator
```
Conservator primește doar `{id, summary, sketch}` pentru candidates marcate `valid: true` — fără `issues` și fără `rationale`. Scorează riscul pe baza sketch-ului, nu a poveștii pe care a spus-o Control. În parallel mode pasul e omis.

**Opțional — diff_size + churn autoprobe.** Pentru schimbări pe cod commited / staged, rulează:
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main            # main..HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Returnează `{files_changed, lines_added, lines_removed}` din `git diff --numstat`. Cu `--churn N`, adaugă `churn.commits_per_file` — semnal pentru `regression_risk` (un fișier cu 8+ commit-uri în ultimele 14 zile e fragil; unul cu 0 e stabil). Când probe-ul e prezent, ancorează `diff_size` la `files_changed/lines_*` și `regression_risk` la distribuția de churn în loc să estimezi. Probe-ul e advisory — `prompts/conservator.md` rămâne autoritativ și nu îl referențiază direct (probe-ul se injectează în context, nu în prompt).

### 5. Aggregate
Rulează:
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — orice candidate cu `risk_score > 0.7` primește veto, indiferent de scorurile celorlalți. În rândul candidate-urilor non-vetoiți, ranking-ul folosește media ponderată `(generator + control + safety)` unde `safety = 1 - conservator` — așa că la egalitate pe celelalte voci, candidatul mai sigur câștigă.

Alte scheme disponibile: `majority`, `weighted`, `risk_adjusted_utility`.

**`risk_adjusted_utility`** — alternativă la `conservative_override` când pragul binar la 0.7 e prea brutal:
```bash
python scripts/aggregator.py --scheme risk_adjusted_utility
```
Calculează `utility(c) = mean(gen, ctrl, 1-cons)` (cu Conservator flip-uit la safety) și aplică penalty sigmoidal centrat la risc=0.5. Fără veto rigid — un candidate cu risc 0.7 nu e disqualified, doar penalizat (~79%). Folosește când ai mulți candidates strânși în jurul pragului de veto și preferi un tiebreaker neted.

**Auto-relax la veto total.** Dacă toți candidates sunt vetoiți, aggregator-ul atașează un bloc `retry_suggested` cu:
- `relaxed_threshold` — prag-ul minim sub care candidate-ul cu cel mai mic risc ar fi supraviețuit (capped la 0.85)
- `lowest_risk_candidate` — candidatul cu risc minim și `would_survive_relaxed` (bool)
- `reason` — sugestie să re-rulezi Generator cu constraint "stay under risk X"

Acțiunea pe `retry_suggested` e a ta (agentul principal), nu automată — un veto total e un semnal important că request-ul poate fi prost formulat sau că toate abordările sunt prea riscante. Decide: re-roll cu constraint mai strict (acceptă mai puține candidate, dar cu risc mai mic), acceptă `chosen: null` (oprește deliberarea), sau întreabă user-ul.

### 5b. Confidence
După aggregation, derivă `confidence` din variance + separation:
```bash
echo '{"candidates": [...], "chosen": "approach_id"}' | python scripts/confidence.py
```
Returnează `{confidence, agreement, separation}`. Folosește valoarea `confidence` în raport — nu mai seta număr magic. Dacă `chosen` e `null` (toți vetoiți), `confidence` e `null` și raportul o lasă așa.

### 6. Report
Asamblează raportul cu:
```bash
cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
```
unde `bundle.json` combină output-urile de la step 2-5b plus `success_criterion`/`verification` din step 1. Schema bundle-ului:
```json
{
  "success_criterion": "...",
  "verification": "...",
  "generator":   {"candidates": [...]},
  "control":     {"verdicts":   [...]},
  "conservator": {"scores":     [...]},
  "aggregate":   {"scheme": "...", "chosen": "...", ...},
  "confidence":  {"confidence": 0.85, ...},
  "telemetry":   {...}
}
```
`build_report.py` derivă `voice_scores` din scoruri brute, asamblează `alternatives` din candidates non-chosen (cu `why_not` din issues Control / risk Conservator), construiește `deliberation_log` în formatul corect, și emite raportul canonic. Asta elimină asamblarea manuală — și clasa de bug-uri "report shape drift" pe care o producea (e.g., câmpuri ratate, log mis-nested).

Pentru raporte skipped (când scope_gate la Step 1.5 a zis `should_skip: true`), bundle-ul e mai scurt: doar `success_criterion`, `verification`, `skipped: true`, `skip_reason`, `signals`. `build_report.py` short-circuitează la shape-ul skipped.

Output JSON final (ce produce `build_report.py`):

```json
{
  "success_criterion": "propoziție testabilă din pasul 1",
  "chosen_approach": "approach_id",
  "reasoning": "scurt rezumat al deciziei",
  "verification": "pasul concret prin care confirmi că success_criterion e îndeplinit (ex: rulează `npm test`, verifică endpoint X răspunde 200, măsoară timp de render)",
  "alternatives": [
    {"id": "...", "summary": "...", "why_not": "..."}
  ],
  "voice_scores": {
    "generator": 0.8,
    "control": 0.9,
    "conservator": 0.4
  },
  "confidence": 0.85,
  "telemetry": {
    "mode": "parallel",
    "passes": 1,
    "voices": {
      "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
      "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 2100},
      "conservator": {"tokens_in":  900, "tokens_out": 180, "latency_ms": 1800}
    }
  },
  "deliberation_log": [
    {"step": "generator", "candidates": [...]},
    {"step": "control", "verdicts": [...]},
    {"step": "conservator", "scores": [...]},
    {"step": "aggregate", "scheme": "...", "result": "..."}
  ]
}
```

Câmpurile `success_criterion` și `verification` sunt **obligatorii** — sunt cerute de Principle #4 din Constitution.

**Telemetry e opțional dar încurajat.** Umple ce poți măsura, omite ce nu poți. În parallel/dialectic mode ai latențe per sub-agent; în sequential nu poți izola token-ii pe voce — pune doar `mode` + total `latency_ms` pe ce ai (sau omite voices). Validator-ul acceptă fields parțiale; `scripts/usage.py` agregă pe ce găsește. Pentru raporte skipped, omite blocul telemetry complet (nu există voci de măsurat — scope_gate-ul e neglijabil).

**Gate de validare** (înainte de a considera raportul final):
```bash
cat runs/<file>.json | python scripts/validate_report.py
```
Exit 0 = OK. Exit 1 = field lipsă/gol sau telemetry malformat; tipărește detaliile pe stderr. Exit 2 = JSON malformat. `chosen_approach: null` e legitim (cazul "all candidates vetoed").

**Acțiuni finale (obligatorii — fără ele deliberarea nu e completă):**
1. **Persistă raportul.** Scrie JSON-ul complet în `runs/YYYY-MM-DD_HHMM_<short-label>.json`. Schema în `runs/README.md`. Fără asta, `priors.py` la deliberarea următoare nu te vede; pierdem feedback loop-ul.
2. **Loghează automat în `FEEDBACK.html` cu outcome confidence-gated.** La finalul Step 6, citește `confidence` din raport și alege calea:

   - **`confidence >= 0.7`** — pickul are agreement și separation suficient; auto-OK fără să întrebi user-ul:
     ```bash
     cat runs/<file>.json | python scripts/log_feedback.py --outcome OK
     ```

   - **`confidence < 0.7`** — întreabă user-ul: *"Confidence sub prag (`<X>`). Vrei să override-ezi `<chosen>`? Alternative din raport: `<alt_id list>`. Răspunde alt_id, 'no', sau 'skip'."* Apoi:
     - `no` → `python scripts/log_feedback.py --outcome OK`
     - `<alt_id>` → `python scripts/log_feedback.py --outcome OVR --override-target <alt_id>` (cu `--user-note "<motiv>"` opțional)
     - `skip` → `python scripts/log_feedback.py` (PEND, default — user-ul închide manual mai târziu)

   - **`confidence` is null** (toți candidates vetoiți) — `python scripts/log_feedback.py` fără flag. Veto total = no decision = no outcome to rate.

   Pragul `0.7` e o decizie de workflow în acest fișier, nu config în script. Schimbarea pragului = o editare aici. `--dry-run` previzualizează linia fără să scrie, în orice combinație de flag-uri.

   Script-ul derivă coloana note automat: `"skipped: <reason>"`, `"all vetoed; relaxed=<X>"`, sau `"<N> cand, <K> vetoed, conf=<X>, mode=<Y>"`. Când outcome e OVR, se append-ează `; override=<target>` și (opțional) nota user-ului.

## Skill maintenance

Următoarele se aplică doar când lucrezi *la* skill (editezi `scripts/*.py`, `prompts/*.md`, `SKILL.md`), **nu** la fiecare deliberare. Sări peste secțiune dacă doar folosești `/max-agent` pe un task.

### Eval harness (la editarea oricărui script deterministic)
Când modifici `aggregator.py`, `confidence.py`, `validate_report.py`, `strip_context.py` sau `dialectic_merge.py`, rulează:
```bash
python scripts/run_evals.py
```
17+ scenarii fixate în `evals/scenarios.json` exersează schemele de aggregator, derivare confidence, validare raport (incluzând skipped + telemetry), proiecția strip_context și merge-ul dialectic. Exit 0 = toate trec; non-zero = ai stricat ceva. Schema scenariilor + cum adaugi cazuri noi: vezi `evals/README.md`. Eval-ul **nu** acoperă vocile LLM (`prompts/*.md`) — pentru regresia lor încă nu există un harness de replay.

### Usage rollup (când ai ~10+ runs cu telemetry)
```bash
python scripts/usage.py                # toate runs/
python scripts/usage.py --last 50      # ultimele 50
```
Returnează totaluri per voce (sum/mean/p50/p95 pentru tokens_in, tokens_out, latency_ms), breakdown per mode (sequential/parallel/dialectic) și câte runs au fost skipped. Util pentru a dovedi că scope_gate salvează cost real, sau a justifica costul 2× al dialectic mode pe schimbări care contează.

### Audit periodic feedback
```bash
python scripts/feedback.py            # stats globale
python scripts/feedback.py --recent 10 --runs
```
Output-ul arată: rata de succes, override-uri recente, ce scheme s-au folosit cel mai des. Ține ca semnal pentru când să ajustezi `prompts/*.md` sau `veto_threshold` (ex: dacă `bad_rate > 0.25` cu keyword recurent în note, ai un tipar real de eșec, nu zgomot).

## Resources

- `prompts/generator.md` — template pentru voce creativă
- `prompts/control.md` — template pentru voce analitică
- `prompts/conservator.md` — template pentru voce skeptică
- `scripts/personalities.py` — rejection sampling pentru ensemble mode
- `scripts/aggregator.py` — 4 scheme de voting + auto-relax la veto total
- `scripts/priors.py` — extrage priori soft din FEEDBACK.html + runs înainte de step 1
- `scripts/validate_report.py` — gate Principle #4 (success_criterion + verification + chosen_approach)
- `scripts/probe_change.py` — ancorare diff_size la `git diff --numstat`
- `scripts/confidence.py` — derivă confidence din variance inter-voci + separation față de runner-up
- `scripts/strip_context.py` — proiectează output-ul voci anterioare la minimul necesar (reduce contaminarea în sequential mode)
- `scripts/scope_gate.py` — auto-detect dacă scope-ul e suficient de mic ca să sari deliberarea (Step 1.5)
- `scripts/dialectic_merge.py` — combină outputs Pass-1 + Pass-2 din dialectic mode într-un payload aggregator-ready, cu `revision_log` per voce
- `scripts/run_evals.py` + `evals/scenarios.json` — regression suite pentru scripturile deterministice (Skill maintenance)
- `scripts/usage.py` — rollup telemetry across `runs/*.json` (Skill maintenance)
- `scripts/log_feedback.py` — auto-append linie în FEEDBACK.html la finalul Step 6 (outcome=PEND, user-ul închide ulterior)
- `scripts/build_report.py` — asamblează raportul canonic dintr-un bundle de output-uri intermediare (Step 6); elimină clasa de bug-uri "report shape drift"
- `agents/max-subagent.md` — definiție de subagent Claude Code pentru invocare prin `Agent(subagent_type="max-subagent", ...)` în context izolat. Delegă la SKILL.md (non-interactive overrides pentru Step 0/1/6). Install: symlink la `~/.claude/agents/max-subagent.md` (vezi fișierul).

## Feedback loop (artefacte)

Skill-ul învață din uz real prin două artefacte. Aici e descrierea lor; *cum* sunt folosite (citite la Step 0, scrise la Step 6, auditate periodic) e prescris în Workflow și Skill maintenance.

- **`runs/`** — JSON complet per deliberare în `runs/YYYY-MM-DD_HHMM_<short-label>.json` (schema în `runs/README.md`). Fișierele sunt gitignored (personale). Citite de `priors.py` (Step 0) și `usage.py` / `feedback.py` (Skill maintenance). Scrise la finalul Step 6.
- **`FEEDBACK.html`** — jurnal manual, o linie per folosire, format `data | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR` (override), `PEND`. Local/personal — gitignored (la fel ca `runs/*.json`), nu shared între mașini. User-ul îl scrie când e cerut la finalul Step 6.

## Parallel voices mode (opt-in)

Default-ul e secvențial: agentul principal joacă toate cele 3 voci în același context. Riscul e cross-contamination — Generator vede ce zice Control înainte de a fi terminat, etc.

Pentru independență reală, dispatch vocile ca **până la 3 sub-agenți Claude rulând în paralel** (tool-ul `Agent`, `subagent_type=general-purpose`).

### Când să folosești
- Schimbarea e suficient de subtilă încât contaminarea între voci ar afecta decizia
- Ai timp/budget să aștepți 3 rulări paralele
- User-ul cere explicit "in paralel" / "parallel voices"

Default-ul (secvențial) rămâne potrivit pentru deliberări rapide și schimbări mici.

### Cum
Un singur message cu **3 Agent calls** (regula superpowers:dispatching-parallel-agents — calls independente într-un singur turn). Fiecare sub-agent primește:
1. `success_criterion` din pasul 1
2. Diff-ul / contextul schimbării
3. Conținutul integral al prompt-ului vocii sale (`prompts/generator.md`, `prompts/control.md`, sau `prompts/conservator.md`)
4. Instrucția de a returna **strict** JSON-ul specificat în prompt — nimic în plus

Sub-agenții nu se văd între ei (asta e ideea). De aceea:
- Generator-ul rulează **primul** (singur sau în paralel cu nimeni — el nu depinde de nimic).
- Control + Conservator pot rula **în paralel între ei** după ce Generator a terminat, primind output-ul lui.

Așadar pattern-ul real e:
1. **Turn 1**: dispatch Generator (1 Agent call). Aștepți candidates.
2. **Turn 2**: dispatch Control + Conservator în paralel (2 Agent calls în același message), ambii primind candidates din Turn 1.
3. **Construire input aggregator**: rulează `dialectic_merge.py` cu `pass2` omis — funcționează identic pentru plain parallel mode, dă `control_score=0.0` candidate-urilor pe care Control le-a marcat `valid: false` și le păstrează în ranking cu scor scăzut. Fără pasul ăsta, ai construi input-ul agregator-ului manual și ai risca să ranchezi un candidate invalid (Conservator, rulând simultan cu Control, l-a scorat — nu știa că e respins). Schema pentru `pass1`-only:
   ```json
   {
     "pass1": {
       "generator":   {"candidates": [...]},
       "control":     {"verdicts":   [...]},
       "conservator": {"scores":     [...]}
     }
   }
   ```
4. Agregi local (`scripts/aggregator.py`) pe output-ul `dialectic_merge` și produci raportul final.

Maximum 3 sub-agenți activi simultan; în practică folosești 1 + 2.

**Captură telemetry per voce (responsabilitatea orchestratorului, nu a sub-agentului).** Sub-agenții nu-și pot măsura tokens cu acuratețe. Orchestratorul (agentul principal) îi măsoară la fiecare Agent call și injectează în bundle:

- `tokens_in` ≈ `len(prompt) / 4` (lungimea prompt-ului trimis sub-agentului, în chars / 4 = aproximare tokens)
- `tokens_out` ≈ `len(response) / 4` (la fel pentru output-ul JSON al sub-agentului)
- `latency_ms` = wall-clock între dispatch și răspuns (timpul real, măsurat de orchestrator)

Output în bundle:
```json
"telemetry": {
  "mode": "parallel",
  "voices": {
    "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
    "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 2100},
    "conservator": {"tokens_in":  900, "tokens_out": 180, "latency_ms": 1800}
  }
}
```

Best-effort: aproximările sunt sub-tokens-API, dar `usage.py` rollup-ul rămâne util pentru tendințe (p50/p95 per voce). Mai bine telemetry aproximat decât zero — fără capturare, parallel mode runs apar ca "0 tokens" în statistici și nu poți justifica costul vs sequential.

### Prompt template pentru un sub-agent
```
Goal: <success_criterion>
Change under review: <diff sau descriere>
Codebase context: <fișiere atinse, limbaj, framework>

Your role and instructions:
<conținutul integral al prompts/<voice>.md>

Return STRICTLY the JSON specified in the "Output format" section above. No prose before or after.
```

### Skip dacă
- Schimbarea e trivială (<10 linii, modul izolat) — overhead-ul nu merită
- Nu ai tool-ul `Agent` disponibil în sesiune
- Vrei să auditezi raționamentul intermediar pe parcurs (sub-agenții returnează doar JSON final)

## Dialectic mode (opt-in, two-pass)

Parallel mode evită contaminarea, dar plătește o altă taxă: vocile **nu se aud niciodată una pe alta**. Dacă Conservator-ul vede ceva ce Generator-ul a ratat, Generator-ul nu mai are șansa să revizuiască. Dialectic mode adaugă o a doua trecere cross-context controlată, fără să sacrifice independența primei runde.

### Pattern
Două passes, fiecare cu 3 sub-agenți paraleli (6 sub-agenți total în 2 turn-uri):

1. **Pass 1 — independent**: identic cu parallel mode (1 + 2 pattern). Cele 3 voci produc output-urile lor inițiale fără să se vadă.
2. **Pass 2 — revision**: fiecare voce primește output-urile *celorlalte două voci* din Pass 1 și răspunde la întrebarea: "Vezi ceva ce vrei să schimbi în propriul output?" Output-ul revizuit (sau confirmarea) e autoritar.

Un singur round de revizuire — fără bucle infinite, fără așteptare de "convergență". Goal-ul nu e consens; e ca fiecare voce să aibă șansa să updateze pe baza evidenței celorlalți.

### Când să folosești
- Decizii subtile unde **o singură voce ar putea schimba opinia** dacă vede ce-au zis celelalte (ex: Conservator-ul flag-uiește un risk score mare → Control-ul, văzând asta, realizează că issue-ul corespunde unei edge case nedeclarate)
- High-stakes unde costul 2× parallel e acceptabil
- Auditare: `revision_log` arată ce a schimbat fiecare voce între passes — evidence că dialectic-ul a mișcat ceva

### Skip dacă
- Schimbarea e simplă — parallel mode e mai ieftin și sufficient
- Vocile sunt deja unanime în Pass 1 (te poți opri opțional, marcând `pass2: null`)
- Nu ai budget pentru 6 sub-agent calls

### Cum
1. **Turn 1**: dispatch Generator (1 Agent call). Aștepți candidates.
2. **Turn 2**: dispatch Control + Conservator în paralel (2 Agent calls). Ambii primesc candidates Pass-1. Salvezi cele 3 outputs ca `pass1`.
3. **Turn 3 (revision)**: dispatch 3 sub-agenți paraleli — câte unul per voce. Fiecare primește:
   - Outputurile **celorlalte două voci** din Pass 1 (nu propriul output — îl re-derivă)
   - Instrucțiunea: "Given what your peers concluded, produce a revised output OR re-emit your original unchanged."
   Salvezi rezultatele ca `pass2`.
4. **Merge & aggregate**:
   ```bash
   cat dialectic_payload.json | python scripts/dialectic_merge.py | python scripts/aggregator.py --scheme risk_adjusted_utility
   ```
   `dialectic_merge.py` folosește Pass-2 ca autoritar (sau cade pe Pass-1 cu flag `fallback_to_pass1` dacă lipsește), generează formatul aggregator-ready și emite `revision_log` cu diff-ul per voce.

### Payload format pentru merge
```json
{
  "pass1": {
    "generator":   {"candidates": [...]},
    "control":     {"verdicts":   [...]},
    "conservator": {"scores":     [...]}
  },
  "pass2": {
    "generator":   {"candidates": [...]},
    "control":     {"verdicts":   [...]},
    "conservator": {"scores":     [...]}
  }
}
```
`pass2` (sau orice voce individuală din el) e opțional — fallback transparent la Pass-1. Pentru a sări revizia complet pentru o voce dacă deja era unanimă, pur și simplu nu o include în `pass2`.

### Cost
Max 6 sub-agent calls în 3 turn-uri (1 + 2 + 3). În practică: 2× parallel mode. Folosește doar când justificat.

## Ensemble mode (opțional)

Pentru schimbări **high-stakes** (migrări DB, modificări de security, refactor mare):

```bash
python scripts/personalities.py 5
```

Generează N=4–6 personalități cu weights random `w ∈ [0.2, 0.49]`, sum = 1.0. Rulează skill-ul de N ori cu personalități diferite, apoi agregă cross-agent prin `--scheme weighted`.

Folosește când o singură deliberare nu e suficientă și vrei diversitate suplimentară.
