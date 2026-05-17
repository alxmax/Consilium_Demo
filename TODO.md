# TODO — sursă unică Consilium (consolidat 2026-05-17)

> Toate TODO-urile + bug-urile repo-ului într-un singur fișier.
> Consolidat din: `TODO.md` (vechi), `TO_DO_Consilium.md` (audit prompts/skill), `BUGS.md` (audit 2026-05-16, 107 findings, anterior gitignored).
>
> Documentul de referință `experiments/New phase senat/todos/SENAT-todo-rol-legi-functii.md` rămâne ca specificație conceptuală (nu e TODO acțional).

## Cuprins

1. [✅ IMPLEMENTAT](#-implementat)
2. [❌ NEIMPLEMENTAT](#-neimplementat)
3. [🤔 DECIZII NEREZOLVATE](#-decizii-nerezolvate)
4. [📋 POST-MERGE VALIDATION](#-post-merge-validation)
5. [🔧 Audit prompts & skill (TO_DO_Consilium #2-#53)](#-audit-prompts--skill)
6. [🐞 Bug-uri (107 din audit 2026-05-16)](#-bug-uri)
7. [🏛 Hotărâri Senate](#-hotarari-senate)
8. [Rollback hooks](#rollback-hooks)

---

## ✅ IMPLEMENTAT

### Senatul ca entitate separată — PR #56, #57, #58
> Branch-uri: `feat/senat-entity`, `feat/senate-tests-html`, `feat/senate-mvp-status`
> Commits: `ca70396`, `d7c2a59`, `3980d90`

- [x] 7 prompturi senatori în `prompts/senators/` (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon)
- [x] `scripts/senate_synth.py` — dispatcher + sinteză vot
- [x] `scripts/test_senate_synth.py` — smoke tests
- [x] Mod `/consilium senate` invocat manual, on-demand only
- [x] Storage în `runs/senate/`
- [x] Documentație în `SKILL.md` cu Laws active/suspended + self-validation disposition
- [x] HTML architecture cu cross-questions schemes

### Senate Laws 2-4 activation — branch `feat/senate-laws-2-3-4`
> Anterior suspendate în MVP; activate ca opt-in multi-round.

- [x] **Law 2 — Cross-questions max 3/rundă**: `cross_questions[]` opțional în output-ul fiecărui senator; synth numără emisiile per senator + emite `law_2_violation` warning peste prag
- [x] **Law 3 — Blocaj resolution**: synth detectează `blocaj_pending: [{go_senator, stop_senator}]`; `blocaj_resolution` în input înlocuiește votul loser-ului cu cel al winner-ului + păstrează `_blocaj_override` marker pentru audit
- [x] **Law 4 — Sinteza doar la final**: `collect_final_outputs(rounds)` ia ultimul vot per senator înainte de tally; `position_changes[]` track-uite cu trigger inferat din cross-Qs
- [x] Schema multi-round în `senate_synth.py` (`{rounds: [...]}`) cu backward compat pe legacy `{senators: {...}}`
- [x] 7 senator prompts extinse cu `cross_questions[]` în output format + secțiune "Cross-questions (multi-round)"
- [x] Orchestrator protocol în `SKILL.md` (pași 4-5 pentru cross-Qs + blocaj)
- [x] 5 tests noi: `multi_round_position_change`, `cross_questions_law2`, `blocaj_pending`, `blocaj_resolution_applied`, `legacy_single_round_compat` (14/14 PASS)
- [x] Status flip în `docs/senate/architecture.md` §9.1 și `architecture.html` §8/§9

### RUND2 architecture — PR #59
> Branch: `feat/rund2-architecture`
> Commit: `44a5cb3`

- [x] **Sequential dispatch**: Conservator → Generator → Control
- [x] Conservator extins: `reversibility`, `magnitude`, `counterparty_risks`, `bias_check`, `meta_recommendation`, `tokens_budget`
- [x] Veto power Conservator (blocant pe ireversibilitate)
- [x] Generator extins: `fallback_scenario`, `coverage_check`, `challenge_upward`, `abstain`
- [x] Vizibilitate selectivă: Generator vede `magnitude`+`counterparty_risks`+`tokens_budget`, NU `meta_recommendation`
- [x] Control extins: `glossary`, `hidden_assumptions`, `disagreements`, `fixed_constraints`, `negotiable_constraints`
- [x] Veto soft Control pe `glossary_fail` + `disagreements: substantial`
- [x] `scripts/aggregator.py` — 8 componente core
- [x] `scripts/vocabulary_map.py` — Wittgenstein dictionar fix
- [x] `scripts/principle_extraction.py` — scripted, blocked pending runs/ maturity
- [x] `scripts/validate_report.py` — extended cu schema RUND2
- [x] `scripts/test_rund2.py` — tests dedicate
- [x] Pass2 prompts: `conservator_pass2.md`, `generator_pass2.md`, `control_pass2.md` (cross-review layer)
- [x] Paralel auto-trigger pe `critical + irreversible`
- [x] Audit periodic la 20 runs (paralel ca cross-check)

### Philosophical voice variants — branch `feat/philosophical-voice-variants` (parțial merged)
> Status reverificat 2026-05-17 — fișiere prezente în main după pull.

- [x] `prompts/control_aurelius.md` — zone-of-control filtering
- [x] `prompts/conservator_confucius.md` — precedent consultation
- [x] `prompts/refiner_deletion.md` — refinement layer (Musk "make it FAST")
- [x] `scripts/precedent_search.py` — pentru Confucius
- [x] `scripts/test_philosophical_voices.py` — tests dedicate

### Senate auto-TODO + auto-transcript
- [x] `scripts/senate_todo.py` — auto-append hotărâri în TODO.md (idempotent)
- [x] `scripts/senate_transcript.py` + `scripts/show_senate_transcript.py` — generator WhatsApp-style HTML transcript
- [x] Integrare în `senate_synth.py` (commit `4755ced`)

---

## ❌ NEIMPLEMENTAT

### Philosophical voice variants — REMAINING

> **Status (audit 2026-05-17 via /consilium):** PR #62 (`c358484`) a livrat 3 variante + script + tests. Wittgenstein și Aurelius (conservator) au fost absorbiți în vocile core în RUND2.
>
> **Livrate** (nu mai sunt TODO): `prompts/control_aurelius.md`, `prompts/conservator_confucius.md`, `prompts/refiner_deletion.md`, `scripts/precedent_search.py`, `scripts/test_philosophical_voices.py` (27 tests PASS), `validate_report.py --strict-philosophical={aurelius-control,confucius}`.

**Closed:**

- [x] ~~**Phase 13 — empirical validation**~~ — ✅ CLOSED (2026-05-17). Vocile țintite (`control_aurelius`, `conservator_confucius`) au fost șterse în `b76e0cb` ("fix(deprecate): remove 4 unvalidated experimentals — Senate-approved"). Validarea empirică nu mai are subiect.
- [x] ~~**Phase 5c — internal question audit**~~ — ✅ CLOSED (2026-05-17). Audit-ul a fost executat în plan-ul `docs/superpowers/plans/2026-05-16-philosophical-voice-variants.md` Task 7.2: verdict acceptable (1 ⚠️ pe Conservator+Aurelius bias_check discreteness, sub pragul 2 ⚠️). 3 din 6 voci auditate au fost șterse în `b76e0cb`; cele 3 întrebări absorbite în vocile core (`control.md` Q1 glossary, `conservator.md` Q1 reversibility, Q4 bias_check) re-verificate 2026-05-17 — same verdict, 1 ⚠️ bias_check, acceptable.

---

### ~~Stale pendings 2026-05-12~~ — ✅ CLOSED (2026-05-17)

> Rezolvate retroactiv via `mark_outcome.py` după audit /consilium (2026-05-17):
> - `add_null_confidence_branch` → OK (documentat în architecture.html / RUND2)
> - `recompute_aggregation_table` → OK (aggregator.py shipped în RUND2 PR #59)
> - `drop_f1_keep_f2_f3` → BAD (loser; F1 a fost shipped în `b90d66e`)
> - `interp_b_ship_subset_f2_f3_only` → BAD (loser; F2-F8 shipped în `2d96d1d`)
> - `ship_f1_only_now` → OK (winner; confirmed user)

---

## 🤔 DECIZII NEREZOLVATE

Din `TODO_RUND2.md` Anexa D — decizii personale care nu blochează implementarea curentă:

- [ ] **Veto budget pentru `meta_recommendation`: 5/lună acceptabil?** Aurelius+Napoleon au propus, dar numărul e arbitrar. Poate vrei 10 sau 3.
- [ ] **Outcome tracking — manual sau automat?** Pentru trading se poate automat din MT4. Pentru altele cere completare manuală. Dacă nu, `principle_extraction` nu se activează niciodată.
- [ ] **Napoleon rămâne senator după empirical validation?** Phase 14B din TODO_RUND2 verifică over-fit la P3. Decide după validare.

Din `TODO_SENAT.md` Anexa D:

- [ ] **Senatori viitori (slot 8 și 9)** — decizi când apar candidați. Reguli: testul P3, specialitate non-overlapping >50%, audit de Senatul existent înainte de adăugare.
- [ ] **Reduci Senat de 7 la 6 dacă pare prea costisitor după 5-10 invocări?**

---

## 📋 POST-MERGE VALIDATION

Pendings empirice după merge-ul RUND2 (PR #59 — `2026-05-16`):

- [ ] **14A — Napoleon validation** pe 5-10 întrebări diverse (operaționale + filozofice + ambigue). Verifică over-fit la P3.
- [ ] **14B — Sequential dispatch validation**: rezultă calibrare mai bună decât paralel vechi pe 10 întrebări reale?
- [ ] **14C — Aggregator decisions validation**: pattern detection pe veto-uri în primele 30 runs.
- [ ] **14D — Generează `experiments/run4-rund2-empirical-validation.html`**

---

## 🔧 Audit prompts & skill

> Sursa: `TO_DO_Consilium.md` (acum consolidat). Items numerotate #2-#53. Ranking impact/efort. Categorii: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch**.

### Status batch-uri

- **#1, #16, #17, #20 dropped** după Consilium triage (`runs/2026-05-15_2236_todo-triage.json`).
- **#9, #18 INVESTIGATE** (user, păstrate pentru decizie ulterioară).
- **#2-#8 ✅ DONE** (descoperite implementate la audit Branches 1-5).
- **#13-#15, #19 ✅ DONE** (branch `feat/feedback-and-quality-loop`).
- **#36-#38 ✅ DONE** (branch `fix/audit-flow-modes-top3`).
- **#51-#53 ✅ DONE** (lessons P3 corrigendum).

### Follow-up eval parity (planificat după parallel-review 0.57 conf)

Branch `feat/eval-parity-rest` cu scenarii pentru:
- `memory.py` tier medium/long/unknown (3 scenarii — cer fixtures `runs/`)
- `audit_feedback.py` orphan detection + `--backfill` idempotency (2 scenarii — cer fixture FEEDBACK.html + runs/*.json)
- `mark_outcome.py` `[confirmed]` marker preservation (1 scenariu — cere fixture FEEDBACK.html)
- `priors.py` `weighted_bad_rate` + `missing_feedback_runs` + `stale_pendings` cutoff (3 scenarii)

Total ~9 scenarii noi. Cere extensie a `run_evals.py` să accepte fixtures de filesystem.

### Open items (Tier 2)

#### 9. Goal-fit check mutat la pasul 1 în Control · Prompt · Mediu · Mic-Mediu · INVESTIGATE
Acum Control face types → logic → tests → style → goal-fit. Dacă candidatul nu adresează success_criterion, primele 4 verificări sunt irosite. Fix: mută goal-fit ca **pasul 0** în Task, înainte de types. Fail fast.

#### 10. Cap pe stacking regression_risk reduction în Conservator · Prompt · Mediu · Mic
Prompt-ul spune `-0.15` pentru test coverage dar nu specifică dacă se aplică și pentru feature flag și rollback < 3 pași simultan. Fix:
```
regression_risk reduction: max cumulative −0.20, regardless of how many
mitigations are present. Document each reduction applied in notes.
```

#### 11. Handling pentru candidați ireversibili by nature · Prompt · Mediu · Mediu
Published API change, migration live — `rollback_recipe` executabil e imposibil. Fix:
```
If rollback is structurally impossible (published API already consumed by clients,
live migration with data writes), replace rollback_recipe with mitigation_steps
and add "irreversible": true at candidate level.
```

#### 12. `probe_change.py` data menționată explicit în Conservator Input · Prompt · Mediu · Mic
`probe_change.py` produce `files_changed`, `lines_changed`, `churn` — date concrete dar prompt-ul nu menționează că le poate primi. Fix: adaugă în `## Input`:
```
Optional: probe data — files_changed, lines_changed, churn_per_file (last N days).
Use to anchor diff_size and regression_risk when present.
```

#### 18. Observe → Think → Act → Learn loop formal · Arch · Mediu · Foarte Mare · INVESTIGATE
Schelet-ul există implicit (Step 1 = Observe, Steps 2-4 = Think, Step 5 = Act, Step 6 = Learn). Formalizarea ar permite restart, enrichment, skip-uri condiționate. Risc: Consilium devine agentic și nedeterminist — contrazice Principiul 2 (Simplicity first). De implementat doar dacă meta-controller (16, dropped) e deja stabil.

### Open items — Audit voci (Trias + parallel-skeptic, sesiunea 2026-05-16)

> Sursa: `runs/2026-05-16_0148_voice_audit_meta.json` (sinteză 2 subagenți, Trias 3-0 unanimous + parallel-skeptic confirmă).

#### 20. Skeptic naming collision — rename `Conservator — Skeptical Voice` → `Risk Assessor` · Prompt · Înalt · Mic
`conservator.md:1` se autotitrează "Skeptical Voice" dar vocea scorează risc, nu correctness. Real-skeptic-ul (uncharitable reading) trăiește în slot-ul `adversarial_*` din Generator. Onboarding hazard real. Fix:
```
# conservator.md:1
# Conservator — Risk Assessor

# + în Mindset:
Skepticism about correctness is Control's job;
skepticism about scope and reversibility is yours.
```
Renaming global la `Skeptic` respins (47 runs în priors + ~12 touchpoints).

#### 21. Fix `meta_critic.conservator_spread` denominator (range-relative) · Skill · Mediu · Mic
`meta_critic.py:82` rescalează `pstdev` prin `MAX_RISK_STDEV = 0.5`. Spread genuin de 0.2/0.3/0.4 produce `pstdev≈0.082`, rescalat 0.164 — flag-uit "weak" deși Conservator a făcut treabă reală. Fix: `stdev / max(max_risk - min_risk, 0.5)`, fallback la 0.5 doar când `range < 0.2`.

#### 22. Fix `meta_critic.control_concreteness` — interzice fallback-ul 40-char · Skill · Mediu · Mic
`meta_critic.py:74-80,139` admite un detail ≥40 chars ca "concret" indiferent de conținut. Fix: cere file/symbol regex match SAU technical claim specific — definit ca referință în backticks (symbol/error class), număr de linie, sau condiție explicită.

#### 23. Codifică formula Conservator `risk_score` în prompt · Prompt · Mediu · Mic
`conservator.md:36` descrie regula reversibility-dominance în proză; implementarea efectivă trăiește în `aggregator.py`. LLM-ul Conservator poate să nu se potrivească. Fix: code block în prompt:
```
risk_score = mean(diff_size, scope_drift, regression_risk, reversibility)
if reversibility > 0.7:
    risk_score = max(risk_score, reversibility)
```

#### 24. Rebalance Architect lens — `conservator 0.21→0.30, control 0.49→0.40` · Skill · Mediu · Mic
`personalities.py:24,29`: Pioneer și Architect au `conservator=0.21`. În coaliția 2-1, weight efectiv pe Conservator e 0.21 — sub baseline 0.33. Fix:
```python
{"generator": 0.30, "control": 0.40, "conservator": 0.30}  # Architect
```

#### 25. `meta_critic.py --strict` default când `mode=trias` · Skill · Mediu · Mic
`meta_critic.py:214-233`: `--strict` enables CI exit-1 dar nu e cablat. Fix: detectează `mode=trias` în input și aplică `--strict` automat; advisory rămâne default pentru parallel/sequential.

#### 26. Lărgește trigger adversarial Generator — adaugă semnal hot-path/many-caller · Prompt · Mediu · Mic
`generator.md:31-35`: trigger pentru `adversarial_*` se aprinde doar la (a) clarity gate 2+ interpretări, sau (b) shared/core code. Fix: adaugă trigger (c):
```
(c) the change touches a function with >3 external callers
    or is on a documented hot path
```

#### 27. Câmp `confidence_in_verdict` în Control + flag meta_critic · Prompt+Skill · Scăzut · Mediu
`control.md:9` cere "verify, don't speculate" dar Control primește doar sketches. Speculația trece silent. Fix: adaugă `confidence_in_verdict: high|medium|low` în schema verdictului; meta_critic flag-uiește orice `valid:true + confidence_in_verdict:low` ca warning.

#### 28. Metrici noi în meta_critic — `pass2_revision_quality` + `personalities_divergence` · Skill · Scăzut · Mediu
Două gap-uri în meta_critic.py:
- Nu auditează dialectic Pass-2 — `peer_evidence` poate fi boilerplate.
- Nu măsoară dacă lentilele Trias produc efectiv divergență.

Fix:
- `pass2_revision_quality`: cere `peer_evidence` >20 chars și non-match cu lista boilerplate.
- `personalities_divergence` (Trias-only): flag advisory când toate 3 personalități converg.

### Open items — Audit flow models

#### 29. Pass-2 schema obligatorie documentată în SKILL.md · Skill · Mediu · Mic
`dialectic_merge._is_dissent_compliant` cere `revision` SAU `maintained` pe fiecare item Pass-2. SKILL.md secțiunea Dialectic nu menționează contractul. Parțial documentat (commit `3d59f39`); mai trebuie extins per voce.

#### 30. Failure-mode section în SKILL.md Parallel · Skill · Înalt · Mic
Sub-agent crash / JSON malformed / timeout nu au recovery path documentat.

#### 31. VOTE_PATTERN_CONFIDENCE ordonare contraintuitivă · Skill · Mic · Mic
`2-0` (veto total dintr-o personalitate) primește 0.75 confidence, `2-1` (dissent activ) primește 0.70. Veto e semnal mai grav.

#### 32. Deduplică _TRIAS_EXPECTED_NAMES · Skill · Mic · Mic
`validate_report.py:161` și `personalities.py:21-37` duplică lista. Fix: import din `personalities.NAMES`.

#### 33. Documentează că `strip_context.py` se skip-uiește în Parallel · Skill · Mic · Trivial
SKILL.md Step 3-4 zice "Sequential: rulează `strip_context.py`" fără să clarifice că Parallel nu are nevoie.

#### 34. Şterge sau wrap deprecated `aggregate_weighted` · Skill · Mic · Mic
`aggregator.py:73` are doar `warnings.warn`. Scoate-l din `SCHEMES` map sau ridică la `DeprecationWarning`.

#### 35. Folosește issue severity în `_voice_score_from_verdict` · Skill · Mediu · Mic
`dialectic_merge.py:88` și `build_report.py:70` scad 0.15 per issue indiferent de severity. Fix: ponderare `0.05 / 0.15 / 0.30` pe `severity: low/medium/high`.

#### 39. scope_gate blocklist extends pentru `*secrets*` folder · Skill · Mic · Trivial
`**/secrets*` matchează `secrets.json` dar nu `with-secrets/foo`. Adaugă `**/*secrets*`.

#### 40. telemetry.voices empty în Parallel → eroare (nu warning) · Skill · Mediu · Trivial
`validate_report.py:146-154` doar emite warning. Orchestrator parallel care uită să captureze telemetry trece gate-ul → `usage.py` skip-uiește runul.

#### 41. Tie-break determinist la `team_vote` duplicate top · Skill · Mic · Trivial
`aggregator.py:277-280` foloseşte `for ... break` pe dict — non-deterministic. Adaugă `raise ValueError` explicit.

#### 42. `signals.files_changed = None` la `CONSILIUM_FORCE_FULL=1` type-safe · Skill · Mic · Trivial
`scope_gate.py:212-213` emite `None` pentru numerics. Fix: emite `-1` sau omite câmpurile.

#### 43. Iterative Dialectic — SPEC fără implementare · Arch · Mediu · Mare
`docs/architecture.html` descrie modul iterative cu N=1..3 runde + convergence stop, marcat `SPEC`. `dialectic_merge.py` acceptă strict `{pass1, pass2}`. Fix: ori implementează schema `{rounds: [...]}` cu convergence detection, ori șterge modul din HTML.

#### 44. Sequential "Chinese wall" iluzoriu — clarify în docs · Arch · Mediu · Mic
Sequential rulează același LLM care joacă 3 roluri în acelaşi context. `strip_context.py` doar curăță prompt-ul. Nu e Chinese wall real. Fix: notă explicită în HTML + SKILL.md.

#### 45. Lens injection validation end-to-end · Skill · Mediu · Mediu
`prompts/<personality>_lens.md` sunt fişiere arbitrare. Niciun test că Pioneer e progress-leaning vs Steward risk-averse. Fix: scenariu eval care rulează un diff cu trade-off conservator-vs-progress.

#### 46. Generator Pass-2 candidate diff semantic în `revision_log` · Skill · Mic · Mediu
`dialectic_merge._diff_candidates` listează `fields: ["sketch", "summary"]` ca "modified" dar nu emite diff propriu-zis. Fix: include payload before/after per field în `revision_log.diffs`.

### Open items — Audit LangGraph/LangChain integration

> Sursa: `runs/2026-05-16_1430_audit_langgraph_langchain.json` (parallel mode, chosen=`do_nothing` conf=0.36 PEND).
> Auditul a respins integrarea profundă: veto pe full rewrite (risk 0.95), invalid pe LangChain output parsers, invalid pe topology-only.

#### 47. `optional_sidecar_visualizer` — `experiments/langgraph_replay/` izolat · Arch · Mediu · Mediu · PROPOSED
Sidecar opțional care vizualizează `runs/*.json` post-hoc. Niciun rol în deliberarea live, niciun import din `scripts/`, venv izolat.

Contracte obligatorii înainte de ship:
1. `experiments/langgraph_replay/` rămâne gitignored sau explicit marcat "not part of the skill"
2. `grep -r 'from scripts\|import scripts' experiments/` returnează zero matches
3. `replay.py` output schema definită: Mermaid cu cel puțin un nod per step din `deliberation_log`

#### 48. Analiză: checkpoint per-step între voci · Arch · Mediu · Mediu · INVESTIGATE
Acum `runs/<id>.json` se scrie o singură dată la Step 6. Dacă Control crash-uiește, pierdem tot output-ul Generator-ului.

Întrebări de explorat:
- Partial `runs/<id>_partial.json` per voce sau directory `runs/<id>/<voice>.json`?
- Cum interacționează cu `audit_feedback.py`?
- Cost/beneficiu: cât de des Control/Conservator eșuează?

Decizie blocată până avem datele.

#### 49. Analiză: streaming / human-in-the-loop între Generator și Control · Arch · Mediu · Mare · INVESTIGATE
După Generator, pause; utilizatorul exclude/editează candidate înainte ca Control + Conservator să le vadă.

Întrebări:
- Mecanism nativ Claude Code de pause + user input între sub-agent calls?
- Cum se loghează intervenția în `runs/*.json`?
- Conflict cu Principle 1 (Think before coding)?

Decizie blocată până cunoaștem disponibilitatea pause/resume.

#### 50. Analiză: time-travel peste `runs/*.json` · Skill · Mic · Mic-Mediu · INVESTIGATE
`scripts/replay_aggregator.py` care citește un run, permite editarea manuală a scorurilor, re-rulează aggregator + confidence.

Întrebări:
- Output: nou run sau stdout?
- Cum interacționează cu `validate_report.py`?

Decizie soft-pozitivă, prioritate scăzută.

### Sumar audit prompts & skill

| # | Titlu | Categorie | Impact | Efort |
|---|-------|-----------|--------|-------|
| 2 | Conservator: risc ≠ valoare netă ✅ DONE | Prompt | Înalt | Mic |
| 3 | Control: standard consistent ✅ DONE | Prompt | Înalt | Mic |
| 4 | Generator: nu te ancora ✅ DONE | Prompt | Mediu | Mic |
| 5 | ID preservation explicit ✅ DONE | Prompt | Mediu | Mic |
| 6 | Shared/core code definit în Conservator ✅ DONE | Prompt | Mediu | Mic |
| 7 | Sketch depth specificat ✅ DONE | Prompt | Mediu | Mic |
| 8 | Control: citește fișierele, nu specula ✅ DONE | Prompt | Mediu | Mic |
| 9 | Goal-fit → pasul 0 în Control (INVESTIGATE) | Prompt | Mediu | Mic-Mediu |
| 10 | Cap stacking regression_risk | Prompt | Mediu | Mic |
| 11 | Candidați ireversibili by nature | Prompt | Mediu | Mediu |
| 12 | probe_change data în Conservator Input | Prompt | Mediu | Mic |
| 13 | Single retry la confidence scăzut ✅ DONE | Skill | Mediu | Mediu |
| 14 | Meta-critic calitate deliberare ✅ DONE | Arch | Înalt | Mare |
| 15 | Feedback din outcome real ✅ DONE | Arch | Înalt | Mare |
| 18 | Observe→Think→Act→Learn formal (INVESTIGATE) | Arch | Mediu | Foarte Mare |
| 19 | Memory tiers formalizate ✅ DONE | Arch | Scăzut | Mare |
| 20 | Skeptic rename: Conservator → Risk Assessor | Prompt | Înalt | Mic |
| 21 | Fix meta_critic.conservator_spread denominator | Skill | Mediu | Mic |
| 22 | Fix meta_critic.control_concreteness 40-char fallback | Skill | Mediu | Mic |
| 23 | Codifică formula Conservator în prompt | Prompt | Mediu | Mic |
| 24 | Rebalance Architect lens weights | Skill | Mediu | Mic |
| 25 | --strict default pe mode=trias | Skill | Mediu | Mic |
| 26 | Lărgește trigger adversarial Generator (hot-path) | Prompt | Mediu | Mic |
| 27 | confidence_in_verdict în Control | Prompt+Skill | Scăzut | Mediu |
| 28 | pass2_revision + personalities_divergence metrics | Skill | Scăzut | Mediu |
| 29 | Pass-2 schema în SKILL.md | Skill | Mediu | Mic |
| 30 | Failure-mode section în Parallel | Skill | Înalt | Mic |
| 31 | VOTE_PATTERN_CONFIDENCE reorder | Skill | Mic | Mic |
| 32 | Deduplică _TRIAS_EXPECTED_NAMES | Skill | Mic | Mic |
| 33 | strip_context skip în Parallel — doc | Skill | Mic | Trivial |
| 34 | Şterge deprecated aggregate_weighted | Skill | Mic | Mic |
| 35 | Severity-aware control score | Skill | Mediu | Mic |
| 36 | Trias telemetry required ✅ DONE | Skill | Înalt | Mic |
| 37 | Steward-aware confidence ✅ DONE | Skill | Înalt | Mediu |
| 38 | Pass-2 silent fallback warning ✅ DONE | Skill | Mediu | Mic |
| 39 | scope_gate blocklist `*secrets*` folder | Skill | Mic | Trivial |
| 40 | Parallel telemetry empty → eroare | Skill | Mediu | Trivial |
| 41 | team_vote tie-break determinist | Skill | Mic | Trivial |
| 42 | scope_gate None signals type-safe | Skill | Mic | Trivial |
| 43 | Iterative Dialectic — SPEC fără implementare | Arch | Mediu | Mare |
| 44 | Sequential Chinese wall — clarify docs | Arch | Mediu | Mic |
| 45 | Lens injection validation end-to-end | Skill | Mediu | Mediu |
| 46 | Pass-2 diff semantic în revision_log | Skill | Mic | Mediu |
| 47 | `optional_sidecar_visualizer` PROPOSED | Arch | Mediu | Mediu |
| 48 | Checkpoint per-step între voci INVESTIGATE | Arch | Mediu | Mediu |
| 49 | Streaming / HITL Generator↔Control INVESTIGATE | Arch | Mediu | Mare |
| 50 | Time-travel peste runs/ INVESTIGATE | Skill | Mic | Mic-Mediu |
| 51 | Skeptic-on-chosen ca pas opțional ✅ DONE | Skill | Înalt | Mediu |
| 52 | "Haiku = anti-fabrication" revizuit ✅ DONE | Docs | Mediu | Mic |
| 53 | Oracle verification pe fab-rate claims ✅ DONE | Arch | Înalt | Mic |

---

## 🐞 Bug-uri

> Sursa: `BUGS.md` (audit 2026-05-16, 4 parallel sub-agents × 2 waves). Anterior gitignored — promovat în TODO.md ca sursă unică.
> **Method:** Per file, 3-lens reasoning (Pioneer / Architect / Steward) inline. ≥2 lenses agreeing required.
> **Total:** 107 bugs · 4 critical · 12 high · 39 medium · 52 low.

### Tally

| Agent | Bucket | Wave 1 | Wave 2 | Total |
|---|---|---|---|---|
| 1 | Voting/decision (6 files) | 9 (0C/0H/2M/7L) | 11 (0C/0H/3M/8L) | **20** |
| 2 | Feedback/persistence (7 files) | FAILED (usage limit) | 21 (3C/3H/7M/8L) | **21** |
| 3 | Context/utility (10 files) | 17 (0C/1H/7M/9L) | 9 (0C/0H/3M/6L) | **26** |
| 4 | Prompts + docs (12 files) | 17 (0C/3H/6M/8L) | 23 (1C/5H/10M/7L) | **40** |
| **Total** | **35 files** | — | — | **107** |

### Highest-impact recommendations (fix-first)

1. **Atomic writes to FEEDBACK.html** — fixes 2 critical (`log_feedback.py:209`, `mark_outcome.py:173`) + medium-severity O(N²) backfill race window cu un helper comun.
2. **VETO threshold alignment** (`render_feedback_html.py:211,217`) — fixes 1 critical; orice drill-down istoric minte despre vetoes.
3. **Pass-2 verdict schema** (`control_pass2.md` + `dialectic_merge.py`) — fixes 1 critical; fără asta, Dialectic mode collapse la control_score=0.0.
4. **`dialectic_merge.py` null risk_score guard** (lines 217, 239) — 1 high; one-line defensive fix prevents whole-merge crash.
5. **Clarity gate prescription reconciliation** (SKILL.md / generator.md / consilium-subagent.md) — 1 high; trei documente prescriu trei acțiuni diferite pentru același trigger.
6. **Subagent doc audit** (`agents/consilium-subagent.md`) — 3 high concentrated here.

### Critical (4)

#### [scripts/log_feedback.py:209] FEEDBACK.html written non-atomically — crash mid-write corrupts long-term memory
- **Type:** error-handling · **Lenses:** steward, pioneer
- **Why:** `append_entry` re-renders entire FEEDBACK.html și scrie cu single non-atomic `write_text`. Crash → fișier truncat → istoric pierdut.
- **Evidence:** `feedback_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")`
- **Fix:** Write to `feedback_path.with_suffix(".html.tmp")` then `os.replace(tmp, feedback_path)`; opțional `.html.bak` first.

#### [scripts/mark_outcome.py:173] FEEDBACK.html written non-atomically — same crash-corruption risk as log_feedback
- **Type:** error-handling · **Lenses:** steward
- **Why:** Identical hazard, mai probabil interactiv (Step 6 retroactive correction).
- **Evidence:** `feedback_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")`
- **Fix:** Share an atomic-write helper între `log_feedback`, `mark_outcome`, `audit_feedback`.

#### [scripts/render_feedback_html.py:211,217] Conservator drill-down marks candidates as VETOED at risk ≥ 0.7 — UI lies
- **Type:** logic · **Lenses:** architect, steward
- **Why:** `aggregator.py` defines `DEFAULT_VETO = 0.8` cu `if risk > veto_threshold`. Renderer hard-codes `>= 0.7` → candidates în `[0.7, 0.8]` sunt arătați "VETOED" deși aggregator i-a lăsat să treacă.
- **Fix:** Import `DEFAULT_VETO` from `aggregator` și folosește `> DEFAULT_VETO`. Mai bine: derivă `vetoed` din `aggregate_result.get("vetoed")`.

#### [prompts/control_pass2.md:43-62 vs dialectic_merge.py:202-216] Pass-2 verdict schema lacks `valid`/`issues` — merge silently computes control_score=0.0
- **Type:** schema-mismatch · **Lenses:** pioneer, architect, steward
- **Why:** control_pass2.md definește `{id, revision|maintained}` fără `valid`, `issues`. dialectic_merge.merge() face `verdict.get("valid")` → falsy → `return 0.0`. Toată aggregation collapsuiește.
- **Fix:** (a) require Pass-2 control verdicts să poarte full Pass-1 verdict shape PLUS revision/maintained, sau (b) change `dialectic_merge.py` să fetch `valid`/`issues` from Pass-1.

### High (12)

#### [scripts/log_feedback.py:162-209] No deduplication / no concurrency lock — re-runs silently duplicate rows
- **Type:** concurrency · **Lenses:** steward, architect
- **Fix:** Fingerprint-based dedup + OS-level file lock (`msvcrt.locking` Windows / `fcntl.flock` POSIX).

#### [scripts/audit_feedback.py:95-117 + priors.py:127-148] `--backfill` silently skips runs colliding by (date, chosen[:40])
- **Type:** logic · **Lenses:** architect, steward
- **Fix:** Use `run_path` as matching key when available; fallback la `(date, chosen, context_hash)`.

#### [scripts/migrate_feedback_md_to_html.py:51-72] Fuzzy match accepts zero-overlap candidates
- **Type:** logic · **Lenses:** architect, steward
- **Fix:** Return `None` când `candidates[0][0] == 0`, sau minimum threshold ≥ 2 tokens.

#### [scripts/dialectic_merge.py:217,239] `float(risk_entry.get("risk_score", 0.5))` crashes on null risk_score
- **Type:** type / error-handling · **Lenses:** architect, steward
- **Fix:** `rs = risk_entry.get("risk_score"); rs = 0.5 if rs is None else float(rs)`

#### [SKILL.md:71 vs prompts/generator.md:38-40] SKILL.md missing `unconventional_*` requirement și `unconventional_skipped` sibling
- **Type:** instruction-conflict · **Lenses:** architect, steward
- **Fix:** Add to SKILL.md Step 2 sentence about unconventional being required by default cu `unconventional_skipped` opt-out.

#### [prompts/control.md:29] Goal-fit fallback id `_no_viable_candidate` — aggregator/build_report doesn't know this synthetic id
- **Type:** schema-mismatch · **Lenses:** pioneer, architect, steward
- **Fix:** Drop fallback din control.md (aggregator handles total veto), OR document că `_no_viable_candidate` must be added as Generator candidate.

#### [prompts/skeptic.md:38-51 vs SKILL.md:336-342] Skeptic output schema lacks formal validator
- **Type:** missing-field · **Lenses:** pioneer, architect, steward
- **Fix:** (a) implement `validate_skeptic.py`, OR (b) rewrite skeptic.md "Validation gate" as orchestrator-side check.

#### [prompts/control_pass2.md:33 + control.md:31] Revised valid:true verdict has no slot for `tests_to_write`
- **Type:** missing-field · **Lenses:** architect, steward
- **Fix:** Add to control_pass2.md: dacă revision flips `valid: false → true` pentru orice candidate other than `do_nothing`, emit full Pass-1 verdict shape în adiție de `revision` metadata.

#### [prompts/pioneer_lens.md:9-15 vs conservator.md:7] Pioneer lens "tolerate moderate risk" conflicts cu Conservator's `risk_score` mandate
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Fix:** Restrict lens prepending la Generator only (change personalities.py `lens_applies_to: ["generator"]`), OR per-voice carve-outs.

#### [agents/consilium-subagent.md:33 vs SKILL.md:236-247] Subagent "Sequential mode only" but SKILL.md says default is parallel
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Fix:** Update consilium-subagent.md description: "...returns canonical runs/<file>.json report. **Note: runs Sequential mode**".

#### [agents/consilium-subagent.md:6] Tools list missing `Write` — persistence relies on shell redirect (brittle on Windows)
- **Type:** schema-mismatch · **Lenses:** pioneer, architect
- **Fix:** Adaugă `Write` la tools list (scope la `runs/` only), OR documentează Windows-encoding gotcha și prescribe `python -X utf8`.

#### [SKILL.md:48 vs generator.md:31 vs consilium-subagent.md:37] Clarity gate has 3 incompatible prescriptions
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Why:** Same trigger, three docs, three actions:
  1. SKILL.md L48: stop and ask user
  2. generator.md L31-35: emit `adversarial_*`
  3. consilium-subagent.md L37: emit `interp_a_*`, `interp_b_*`
- **Fix:** Reconcile: distinguish "ambiguity Generator can disambiguate" from "ambiguity requiring user input".

### Medium (39)

#### [scripts/aggregator.py:54-67] `aggregate_majority` sort crashes with TypeError on (mean, -stdev) tie
- **Lenses:** architect, pioneer, steward · **Fix:** Insert stable tiebreaker before `c` (enumerate index). Same exposure în `aggregate_weighted` (line 97).

#### [scripts/build_report.py:64-75] `_voice_scores_for` silently zeros control_score when chosen has no verdict
- **Fix:** Raise/warn când `verdict == {}` after lookup, sau surface missing-verdict ca distinct null/sentinel.

#### [scripts/build_report.py:215-222] `_default_reasoning` mislabels Trias fragmentation as "all candidates vetoed"
- **Fix:** Branch on `scheme == "team_vote"` + `vote_pattern`. Fragmentation: "deliberation fragmented (vote_pattern=…); orchestrator must intervene".

#### [scripts/validate_report.py:170-174] `_validate_trias` iterates fields on personality entry without verifying dict
- **Fix:** `if not isinstance(p, dict): errors.append(...); continue`.

#### [scripts/validate_report.py:138-155] `_validate_telemetry_required` only enforces voices for "parallel" mode, not Trias
- **Fix:** `mode in ("parallel", "trias", "dialectic", "trias_split", "parallel_skeptic", "dialectic_skeptic")`.

#### [scripts/log_feedback.py:188,205-206] Fingerprint truncates context to 30 chars — distinct deliberations share drill-down run_path
- **Fix:** Include full context (sau `run_path`) în fingerprint, sau key sidecar map by `run_path` direct.

#### [scripts/log_feedback.py:146] OVR outcome with missing --override-target produces silent no-op
- **Fix:** Raise `ValueError("--outcome OVR requires --override-target <alt_id>")`.

#### [scripts/mark_outcome.py:83-91] `_annotate_note` not idempotent — duplicates `outcome_reason=` entries
- **Fix:** Filter existing `outcome_reason=` parts before appending.

#### [scripts/audit_feedback.py:116] Backfill performs N full read-render-write cycles — O(N²) work
- **Fix:** Batch backfill — accumulate Entry objects, render and write ONCE atomically.

#### [scripts/render_feedback_html.py:258-261] JSONDecodeError silently downgraded to "no detailed run data"
- **Fix:** Render dedicated `<div class="stub error">corrupted run JSON: <name></div>`.

#### [scripts/migrate_feedback_md_to_html.py:30] TOKEN_RE is ASCII-only — Romanian diacritics never tokenize
- **Fix:** `re.compile(r"[^\W\d_]{4,}", re.UNICODE)`.

#### [scripts/test_feedback_html.py:61-87] Test depends on tracked run file — couples tests to mutable session data
- **Fix:** Create temp directory with synthetic run JSON.

#### [scripts/test_feedback_html.py:1-225] Coverage gaps — no tests for log_feedback dedup, mark_outcome, audit_feedback, sidecar map
- **Fix:** Add dedup test, sidecar map round-trip, mark_outcome și audit_feedback happy-path.

#### [scripts/scope_gate.py:192-220] CONSILIUM_FORCE_FULL overridden by config load failure
- **Fix:** Move env override check to top of `main()`, before `load_config`.

#### [scripts/priors.py:197-203] `find_stale_pendings` surfaces entries with empty/missing dates
- **Fix:** Positive guard: `... and e.get("date", "") and e["date"] < cutoff`.

#### [scripts/dialectic_merge.py:124-126] `validate_input` strictly requires all 3 voices in pass1 (uses `sys.exit`)
- **Fix:** Tolerate missing voices as `{}` in `merge()`, sau raise în loc de `sys.exit`.

#### [scripts/memory.py:104-114] `--n` cap is ignored when `--query` is set
- **Fix:** Apply `[-n:]` after filtering în both tiers.

#### [scripts/run_evals.py:49-55] `subprocess.run(text=True)` uses platform encoding for stdin/stdout
- **Fix:** Pass `encoding="utf-8"` și `PYTHONIOENCODING=utf-8` în `env=`.

#### [scripts/utils.py:50-65] `validate_keys` calls `sys.exit(1)` — fatal for in-process callers
- **Fix:** Raise `ValidationError`; convert to exit code only în `main()` wrappers.

#### [scripts/strip_context.py:51,61] `data.get("candidates"/"verdicts")` crashes on explicit `null` or non-list
- **Fix:** `candidates = data.get("candidates") or []`; isinstance guard.

#### [scripts/probe_change.py:60-84] `parse_numstat` mis-handles rename syntax `{old => new}`
- **Fix:** Pass `--no-renames` to `git diff --numstat`, sau parse și expand.

#### [scripts/dialectic_merge.py:122-126] `validate_input` accepts `pass2: [...]` (list) but `merge()` crashes
- **Fix:** `if "pass2" in payload and not isinstance(payload["pass2"], dict): exit/raise`.

#### [scripts/usage.py:96,120] Strict `isinstance(int)` silently drops `tokens_in: 5.0` (float JSON values)
- **Fix:** `isinstance(vdata[f], (int, float)) and not isinstance(vdata[f], bool)`.

#### [SKILL.md:108-110] Confidence input contract for null chosen says wrong thing
- **Fix:** Reword to "câmpul `confidence` din răspuns e `null`" + add "Step 5d se sare în acest caz".

#### [SKILL.md:240 + Step 5 (parallel)] Parallel mode never mentions Step 5b/5c/5d before Step 6
- **Fix:** Add to Parallel section: "Continuă cu Step 5b → 6; capturează tokens/latency per sub-agent dispatch".

#### [SKILL.md:286-294 (Trias workflow)] Workflow doesn't show JSON schema for Trias report
- **Fix:** Add "Output JSON" mini-schema example în Trias section.

#### [prompts/generator.md:47-74 Output format] Example JSON missing `adversarial_skipped` / `unconventional_skipped` siblings
- **Fix:** Add second example: `{"candidates": [...], "adversarial_skipped": "goal unambiguous", "unconventional_skipped": "trivial doc fix"}`.

#### [prompts/conservator.md:39] Cumulative cap -0.20 vs quality-progress math doesn't add up
- **Fix:** "Apply up to two mitigations; cap total at -0.20. After mitigation 1 (-0.15), budget for mitigation 2 is -0.05 max." Mirror în pass2.

#### [prompts/generator_pass2.md] Pass-2 generator content shape ambiguous — missing summary/sketch/rationale
- **Fix:** Update generator_pass2.md să require full candidate fields (`summary`, `sketch`, `rationale`).

#### [prompts/control_pass2.md (entire)] Pass-2 schema has no escape hatch for `_no_viable_candidate` fallback
- **Fix:** Allow emission de noi synthetic verdicts în Pass-2, OR drop synthetic mechanism entirely.

#### [prompts/pioneer_lens.md/architect_lens.md/steward_lens.md vs SKILL.md] Lens prompts: no link from `voice_bias: prepended` to score-weighting
- **Fix:** Footer to each lens: "Your voice output will be re-weighted by the personality's aggregator weights — focus on perception-shift în your role."

#### [prompts/architect_lens.md:13 vs conservator.md L11] Architect lens "Weight test coverage heavily" overlaps with Control role
- **Fix:** Carve-out: "When applied to Conservator, 'test coverage' bias affects only the `regression_risk` quality-progress adjustment — do NOT inflate risk_score for absent tests."

#### [prompts/steward_lens.md:13 vs generator.md:9] Steward lens "Favor minimal-scope" suppresses Generator divergence
- **Fix:** Per-voice guidance: "When applied to Generator: still produce full 3-5 candidate spread, but order candidates with smaller-blast-radius first; do NOT suppress big-blast-radius candidates."

#### [agents/consilium-subagent.md:40 + 38] Final-message contract: "exactly that file's contents" but description adds extra top-level keys
- **Fix:** Define `subagent_notes` ca optional documented field în validate_report.py și SKILL.md.

#### [agents/consilium-subagent.md:38 vs SKILL.md:163-165] Step 6 confidence override delegated to "no --outcome flag" — different from SKILL.md null branch
- **Fix:** "Use `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json` with no `--outcome` for both confidence < 0.7 and null cases."

#### [agents/consilium-subagent.md:14-23] Working directory setup uses bash export — Windows PowerShell can't execute verbatim
- **Fix:** Add PowerShell alternative, sau wrap în launcher.

#### [prompts/conservator.md:49 vs scripts/aggregator.py] "Matches aggregator.py's expectation" claim is false
- **Fix:** Reword: "There is no automated check that this rule was applied — keep it disciplined manually."

#### [SKILL.md:39 Bootstrap step] "Citește contractele celor 3 voci" enumerates only 3 — skeptic.md and lens prompts not bootstrapped
- **Fix:** Update Step 0: "Citește contractele necesare modului: minimum 3 core; Dialectic adaugă `*_pass2.md`; Trias adaugă `<personality>_lens.md`; skeptic modes adaugă `skeptic.md`."

#### [prompts/generator.md:31 + 40] adversarial/unconventional rationale overlap silently disables anti-stagnation
- **Fix:** Tighten (a): "Skip unconventional ONLY when adversarial ALSO varies on a non-scope axis."

### Low (52)

#### [scripts/aggregator.py:148-156] `auto_relax` retry_suggested emits non-actionable suggestion când lowest_risk exceeds RELAXED_VETO_CAP
- **Fix:** Omit `retry_suggested` sau replace cu `escalation_required` când `lowest_risk > RELAXED_VETO_CAP`.

#### [scripts/aggregator.py:239-309] `aggregate_team_vote` hardcodes abstain reason, losing per-personality context
- **Fix:** `abstained.append({"name": p["name"], "reason": p.get("abstain_reason") or "all candidates vetoed"})`.

#### [scripts/build_report.py:114-131] `_alternatives` emits misleading why_not when chosen=None
- **Fix:** Când chosen=None, set why_not based on candidate's actual veto/risk record.

#### [scripts/build_report.py:174] `int(bundle.get("alternatives_limit", 3))` raises on explicit None
- **Fix:** `alt_limit = int(bundle.get("alternatives_limit") or 3)`.

#### [scripts/build_report.py:78-91] `_why_not` slices `first.get("detail")` with `[:80]` without verifying string
- **Fix:** Add `isinstance(first.get("detail"), str)` guard.

#### [scripts/build_report.py:128-130] `_alternatives` off-by-one: `alternatives_limit=0` emits 1 alt
- **Fix:** Check `if len(out) >= limit: break` BEFORE append, sau `if limit <= 0: return []`.

#### [scripts/build_report.py:206] aggregate variable reassigned with subtly different semantics
- **Fix:** Remove reassignment on line 206, reuse existing local.

#### [scripts/validate_report.py:158] VOTE_PATTERN_REGEX accepts impossible 3-voter patterns
- **Fix:** Tighten regex sau add post-match sum check.

#### [scripts/validate_report.py:164-201] `_validate_trias` early-returns on personalities shape failure
- **Fix:** Replace `return` cu flag; checks should run anyway.

#### [scripts/validate_report.py:164-201] `_validate_trias` doesn't verify weights sum to 1.0 sau lens is a string
- **Fix:** Add weights-sum check + `isinstance(lens, str)` check.

#### [scripts/meta_critic.py:162-178] `conservator_spread` returns 0.0 for single candidate, falsely triggering "shrug" flag
- **Fix:** Return None for single-candidate; skip flag când spread is None.

#### [scripts/meta_critic.py:137-139] `_issue_is_concrete` raises TypeError on non-string detail
- **Fix:** `if not isinstance(detail, str): return False`.

#### [scripts/meta_critic.py:82] MAX_RISK_STDEV=0.5 under-normalizes for N≥3
- **Fix:** Compute as function of N: `max_stdev = sqrt((n//2) * (n - n//2)) / n`.

#### [scripts/retry_context.py:103-119] `_grep_patterns` appends `\(` suffix to dotted symbols that aren't callable
- **Fix:** Only append `\(` for symbols matched by SYMBOL_CALL_RE.

#### [scripts/retry_context.py:65,99,103-110] `extract_targets` accepts multi-word backtick "symbols" yielding non-grep-able patterns
- **Fix:** Tighten `BACKTICK_RE` la `[\w.]{2,40}` sau filter quoted entries cu whitespace.

#### [scripts/log_feedback.py:108-109,116] `bool` slips past `isinstance(x, (int, float))` and prints as `1.00`/`0.00`
- **Fix:** Exclude bools: `isinstance(x, (int, float)) and not isinstance(x, bool)`.

#### [scripts/mark_outcome.py:144-147] Run-path match falls back to filename-only — can mis-match rows
- **Fix:** Match by `name` only când `wanted` is bare filename; altfel require exact `as_posix()` equality.

#### [scripts/audit_feedback.py:111] Backfilled row inherits today's note tense
- **Fix:** Append `; backfilled` marker la note text.

#### [scripts/feedback.py:1-9,106] Docstring still describes FEEDBACK.md while code reads FEEDBACK.html
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [scripts/feedback.py:27] ROW_RE assumes `class="entry"` is first attribute of `<tr>` — implicit renderer coupling
- **Fix:** Order-agnostic regex `<tr[^>]*class="entry"[^>]*>`, sau regression test.

#### [scripts/migrate_feedback_md_to_html.py:117-120] `md_path.rename(bak)` raises on Windows if .bak exists
- **Fix:** Use `os.replace(md_path, bak)`, sau check `bak.exists()` before writing HTML.

#### [scripts/test_feedback_html.py:176] `import json` placed mid-file with `# noqa: E402` — fragile order
- **Fix:** Move import to top of file.

#### [scripts/scope_gate.py:213] CONSILIUM_FORCE_FULL emits sentinel `-1` signals not in documented schema
- **Fix:** Use `0` cu `"reason": "...override..."`, sau add documented `"forced": true` flag.

#### [scripts/priors.py:1] Docstring references `FEEDBACK.md` but code uses `FEEDBACK.html`
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [scripts/priors.py:117-149] `find_missing_feedback_runs` truncates `chosen` to 40 chars enabling collisions
- **Fix:** Use full chosen string, sau document truncation cu longer cap (≥80).

#### [scripts/feedback.py:90-99] `parse_runs` swallows JSON errors silently with no diagnostic
- **Fix:** Emit stderr warning for skipped files.

#### [scripts/dialectic_merge.py:142] Diff includes `revision`/`maintained` fields, producing noisy "modified" entries
- **Fix:** Filter `BOOKKEEPING = {"revision", "maintained"}` from diff keys.

#### [scripts/memory.py:125] Long tier `"total"` reports filtered count, not source total
- **Fix:** Compute `parse_feedback(FEEDBACK)` length, return as `"total"`.

#### [scripts/run_evals.py:97-103] No type-check on loaded scenarios; dict input crashes downstream
- **Fix:** `if not isinstance(scenarios, list): print(..., file=sys.stderr); return 2`.

#### [scripts/utils.py:50] `validate_keys` doesn't verify `data` is a dict
- **Fix:** `if not isinstance(data, dict): raise/exit with clear message`.

#### [scripts/probe_change.py:87-97] `_commit_count` silently returns 0 on git failure
- **Fix:** Distinguish via sentinel (`-1` sau None) și log error to stderr.

#### [scripts/usage.py:91-99] Mode-level latency_ms summed across voices is misleading for parallel mode
- **Fix:** Track latency_ms as `max` for parallel mode, sau document field.

#### [scripts/strip_context.py:61,67] `c["id"]` / `v["id"]` raises KeyError on malformed inputs
- **Fix:** Use `c.get("id")` și skip entries cu falsy id.

#### [scripts/probe_change.py:65-67] Tab-separated numstat parser silently drops paths containing tabs
- **Fix:** `parts = line.split("\t", 2)` sau pass `-z` to git și split by null bytes.

#### [scripts/scope_gate.py:83-98] Case-sensitive `fnmatchcase` lets lowercase `dockerfile` bypass blocklist — "fails open"
- **Fix:** Case-insensitive variant for known-case-insensitive patterns.

#### [scripts/scope_gate.py:91-98] Blocklist patterns with backslashes never match anything
- **Fix:** `pattern = pattern.replace("\\", "/")` mirroring path normalization.

#### [scripts/personalities.py:21-37,84] PERSONALITIES is mutable module-level list; bulk-emit path doesn't deep-copy
- **Fix:** `MappingProxyType` for immutability, sau `[copy.deepcopy(p) for p in PERSONALITIES]`.

#### [SKILL.md:144] voice_scores schema example shows 0.0 floats — Generator score never produced by Generator voice
- **Fix:** Add parenthetical: "voice_scores e derivat de `build_report.py`, nu emis de voci direct."

#### [SKILL.md:206 + Resources table] dialectic_merge.py description omits silently_dropped recovery
- **Fix:** Skip (cosmetic), sau augment Resources table description.

#### [SKILL.md:177-180] Eval harness skill_maintenance lists dialectic_merge.py but personalities.py omitted
- **Fix:** Add `personalities.py` la trigger list at SKILL.md L178.

#### [prompts/generator.md:45 vs dialectic_merge.py:101-112] adversarial_* gets generator_score=0.5; unconventional_* gets 1.0
- **Fix:** Add note în generator.md: "unconventional_* compete on equal footing in voice scoring; adversarial_* și do_nothing get 0.5 generator-score handicap."

#### [prompts/control.md:9] "category: 'types', detail: 'unverifiable — file not accessible'" — no way to emit unverifiable for valid:true candidate
- **Fix:** Add: "When emitting unverifiable issue, prefer `valid: true` și put note în `notes` rather than `issues`."

#### [prompts/conservator.md:51 + SKILL.md:87] rollback_recipe threshold 0.3 — Pass-2 conservator doesn't restate
- **Fix:** Add explicit instruction în conservator_pass2.md: if Pass-1 risk < 0.3 și Pass-2 ≥ 0.3, include new rollback_recipe în `what_changed` prose.

#### [prompts/skeptic.md:48 Output format] `failure_mode` required but no enumerated vocabulary beyond meta_scope_mismatch
- **Fix:** Document expected vocabulary: `regression_risk_uncovered | edge_case_drop | scope_creep | meta_scope_mismatch | ...`.

#### [prompts/generator_pass2.md vs SKILL.md:271] Pass-2 generator schema mismatch
- **Fix:** Reword SKILL.md L271 to clarify revision is metadata wrapper, not new content.

#### [prompts/control_pass2.md:35] Rule misnamed — Conservator risk *can* surface a correctness concern
- **Fix:** Reword: "Don't revise valid:true because Conservator's aggregate score is high. DO revise if Conservator's factors.regression_risk notes name a concrete failure path."

#### [prompts/pioneer_lens.md/architect_lens.md/steward_lens.md] `voice_bias: prepended` front-matter declared but no code reads it
- **Fix:** Remove front-matter (no consumer), sau wire into orchestrator template.

#### [agents/consilium-subagent.md:60] Subagent says "appends to runs/ and FEEDBACK.md" — project uses FEEDBACK.html
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [agents/consilium-subagent.md:5 model:sonnet vs SKILL.md:251 Sonnet 4.6 default] Model declared as "sonnet" — alias resolves to latest
- **Fix:** Either pin la `claude-sonnet-4-6-...` for reproducibility, sau document subagent tracks alias.

#### [prompts/skeptic.md:46 + 67] `quoted_scenario` typed inconsistently
- **Fix:** Replace `"Optional: '...' OR null"` literal cu comment-style marker.

#### [SKILL.md:69 "3-5 candidate"] Generator candidate budget tension with mandatory roles
- **Fix:** Bump upper bound la 6, sau clarify mandatory roles count toward 3-5 budget.

#### [SKILL.md:104 vs SKILL.md:89] Aggregator description omits `risk_score > veto_threshold` veto semantics
- **Fix:** Reword: "veto la `risk_score > 0.8` (strict; 0.80 exact NU e vetoat, 0.81+ DA)".

### Wave tracker

| Agent | Bucket | Wave 1 | Wave 2 |
|-------|--------|--------|--------|
| 1 | Voting/decision (6 files) | done (9: 0H/2M/7L) | done (+11: 0H/3M/8L) |
| 2 | Feedback/persistence (7 files) | FAILED (0 bugs, usage limit) | done (+21: 3C/3H/7M/8L) |
| 3 | Context/utility (10 files) | done (17: 1H/7M/9L) | done (+9: 0H/3M/6L) |
| 4 | Prompts + docs (12 files) | partial (17: 3H/6M/8L, ~7/12 files) | done (+23: 1C/5H/10M/7L) |

**Total runs:** 8 (4 agents × 2 waves), with 1 wave-1 failure (Agent 2). Cap reached per user instruction.

---

## 🏛 Hotărâri Senate

> Auto-append din `senate_synth.py` via `senate_todo.py`. Format: GO/MODIFY/STOP per senator.
>
> **Status (audit 2026-05-17):** Senator critiques marked `[DEFERRED]` per item — feedback on never-executed audit proposals ("flow-and-modes-audit"). Lighter touch: păstrăm în TODO pentru referință, dar nu sunt action items live. Re-evaluează când re-deschizi propunerea sau când `senate_todo.py` produce alte blocuri.

### Hotărârea Senate — phase1-deeply-split-plus-laws-mapping · 17 Mai 2026 · GO (GO 5 · MODIFY 2 · STOP 0)

> **Propunere:** Phase 1 (3 changes): P1.1 augment docs/senate/architecture.md §8.1 table (5 existing Senate Laws) with column mapping each Law to one of the 4 Consilium Constitution Principles. P1.2 add DEEPLY_SPLIT …

- [ ] **[WITTGENSTEIN]** Three operational definitions required: (1) voters_present — count of senators with non-null ballot; specify whether ABSTAIN counts toward quorum and add abstain_votes variable in formula; (2) threshold 3 must be derived (e.g., floor(quorum/2)+1 = 3 when quorum=5) or explicitly committed as constant with rationale in code comments; (3) Principle mapping table needs caption stating mapping criterion (e.g., 'each Law maps to the Principle whose violation it primarily prevents') — otherwise column is editorial opinion, not auditable.
- [ ] **[DIMON]** P1.2 must include co-changes to: (a) senate_transcript.py — add DEEPLY_SPLIT to VOTE_COLORS with distinct color (e.g., orange #f07d00); (b) senate_todo.py — add explicit DEEPLY_SPLIT branch emitting polarization-signal line in TODO.md. Without these, DEEPLY_SPLIT is a verdict synthesizer emits but downstream consumers render silently wrong. Additionally P1.3 should add negative test confirming 4-3 + valid blocaj_resolution resolving to 5-2 does NOT produce DEEPLY_SPLIT.

### Hotărârea Senate — bundle-2-senators-plus-5-improvements · 17 Mai 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Propunere:** Bundle of 6 modifications to consilium Senate mode: A) add 2 new senators (Deming statistical-discipline, Tacitus retrospective-historian); B.1) codify Laws 1-4 in SKILL.md mapped to 4 Constitution Pr…

- [ ] **[WITTGENSTEIN]** Supply machine-executable definitions: (1) 'OK outcome' as ground truth for hit_rate (source + time window); (2) explicit boolean formula for DEEPLY_SPLIT trigger; (3) fixed JSON schema for cross_questions[] contract; (4) code-level definition of 'paragraph present'.
- [ ] **[AURELIUS]** Approve Phase A (2 new senators) + Phase B.1-2 (Laws + DEEPLY_SPLIT + tests). Defer B.3-5 (predispatch, calibration, round.py) until runs/senate/ has >=20 entries to justify automation cost and validate calibration data.
- [ ] **[CONFUCIUS]** Critical findings: (1) Laws are already 1-5 in docs/senate/architecture.md §8.1, NOT 1-4 — proposal conflicts with existing 5-Law structure (Raspuns obligatoriu / Cross-Q / Blocaj / Sinteza la final / Auditabilitate); (2) runs/senate/ has only .gitkeep, zero real runs — calibration script orphaned; (3) SENATORS hardcoded 7-tuple in senate_synth.py + test asserts 'all 7 prompts' — silent non-dispatch risk if new senators not wired atomically; (4) DEEPLY_SPLIT threshold defined for N=7 patterns but N=9 has different distributions (5-4, 4-3-2); (5) cross-questions Law 2 was explicitly deferred 'after >=3 real invocations'.
- [ ] **[SOCRATE]** Three load-bearing assumptions must be declared: (1) minimum corpus size for senate_calibration.py validity — add guard + documentation; (2) decision rule for DEEPLY_SPLIT verdict (what user/orchestrator does on receipt) — must be explicit in SKILL.md, not implicit; (3) pre-dispatch Haiku gate semantics (hard block vs soft annotation) — implementation differs significantly between the two.
- [ ] **[MUSK]** Delete senate_predispatch.py (replace with one SKILL.md callsite note). Delete docs/senate/ subtree (move essential diagram to SKILL.md). Merge Deming's data-discipline into Musk's prompt (no new senator file, count stays at 8 not 9). Replace senate_calibration.py with --by-senator flag on existing priors.py. Keep: tacitus.md, Laws codification (reconcile with existing 5), DEEPLY_SPLIT, senate_round.py, test updates. Net: 2 new files instead of 7-8, ~150-200 lines instead of 400-600, 8 senators instead of 9.
- [ ] **[DIMON]** Before GO: (1) senate_round.py must validate cross_questions[] schema and log visible warning (not silent skip) when malformed; (2) DEEPLY_SPLIT threshold must cover 4-3-2 and 5-4 distributions minimum, with unit test per pattern; (3) senate_calibration.py must handle missing/empty runs/senate/ gracefully with explicit error+exit code, not crash or silent zero-output; (4) senate_predispatch.py must define fallback (proceed or abort) on unrecognized Haiku output. 5 silent failure modes identified and unaddressed.
- [ ] **[NAPOLEON]** Unbundle into 2 phases. Phase 1 ship now: Laws codification + DEEPLY_SPLIT + tests (~1-2 files, ~80-120 lines, ~1-2h, zero runtime cost increase). Phase 2 defer: Deming + Tacitus + senate_calibration.py + senate_round.py + senate_predispatch.py + docs — activate only after >=10 senate runs exist to justify 25-35% per-invocation cost increase and give calibration meaningful data.

### Hotărârea Senate — test-auto-todo · 16 Mai 2026 · UNREACHABLE (GO 2 · MODIFY 0 · STOP 0)

> **Propunere:** test proposal
> **Absenți:** aurelius, confucius, dimon, napoleon, socrate

_Nicio cerere de modificare înregistrată._

### Hotărârea Senate — flow-and-modes-audit-r2 · 16 Mai 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Propunere:** Evalueaza toti pasii workflow (0,1,1.5,2,3,4,5,5b,5c,5d,6) si toate modurile (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) pentru a determ…

- [ ] **[DEFERRED]** **[WITTGENSTEIN]** Propunerea nu e auditabila in forma curenta: termenii-cheie ai intrebarilor (a), (b), (c) nu au definitii operationale verificabile. Inainte de implementare: (1) metrica pentru load-bearing; (2) metrica pentru use-case distinct vs redundant; (3) criteriu de eliminare vs deprecare pentru sectiunile cu probleme documentate.
- [ ] **[DEFERRED]** **[AURELIUS]** Redu scopul propunerii la o intrebare operationala concreta: care moduri cu 0 runs pot fi eliminate fara risc contractual? Aceasta poate fi rezolvata cu Sequential sau un singur agent focal (Musk/Napoleon), nu cu Senate complet. Daca decizia de eliminare are consecinte ireversibile, atunci Senate e justificat — dar numai pentru decizia de stergere, nu pentru audit-ul preliminar.
- [ ] **[DEFERRED]** **[CONFUCIUS]** Conditia non-blocanta din runda 1 partial satisfacuta. Cerinte suplimentare: (1) demotarea Step 5c necesita rezolvarea precedentului neimplementat din runs/2026-05-16_0200_voice_audit_skeptic.json; (2) colapsul Step 5d in skeptic_on_chosen trebuie sa pastreze functia de context enrichment sau sa accepte pierderea cu rationale documentat.
- [ ] **[DEFERRED]** **[SOCRATE]** Propunerea trebuie sa declare: (1) criteriul pozitiv pentru load-bearing — nu doar absenta efectului negativ; (2) daca usage count e criteriu primar sau proxy; (3) daca precedentul RUND2 e argument de autoritate sau exista justificare structurala transferabila. Fara aceste declaratii, auditurile opereaza pe asumptii nerostite.
- [ ] **[DEFERRED]** **[MUSK]** DELETE: Step 5c, Step 5d, parallel_skeptic, dialectic_skeptic, trias_split, principle_extraction.py, RUND2 duplicate sections. SIMPLIFY: Dialectic (demotare la experimental). KEEP: tot restul. Implementare secventiala, nu simultana — un mod per commit pentru a testa regresii.
- [ ] **[DEFERRED]** **[DIMON]** Propunerea trebuie sa adreseze explicit: (1) protocol de deprecare pentru scripturi care raman pe disc dupa eliminarea din contract (rename la *.deprecated.py sau guard INACTIVE flag); (2) versionarea schemei runs/*.json pentru a distinge runs produse cu workflow vechi de cele cu workflow nou; (3) specificarea explicita daca trigger-ul automat al skeptic-on-chosen (banda [0.5, 0.7]) ramane activ dupa consolidare si unde in cod traieste aceasta logica.
- [ ] **[DEFERRED]** **[NAPOLEON]** Narrowing obligatoriu: (1) excludeti din audit modurile cu <2 runs reale; (2) separati analiza pasilor workflow de analiza modurilor in doua deliberari distincte; (3) amanati al doilea run senate pe aceeasi sesiune. Daca continuati acum, limitati la: Sequential vs Parallel (40 runs combinat) + maxim 2 pasi load-bearing din 11.

### Hotărârea Senate — flow-and-modes-audit · 16 Mai 2026 · MODIFY (GO 1 · MODIFY 5 · STOP 0)

> **Propunere:** Evalueaza toti pasii workflow (0,1,1.5,2,3,4,5,5b,5c,5d,6) si toate modurile (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) pentru a determ…
> **Absenți:** napoleon

- [ ] **[DEFERRED]** **[WITTGENSTEIN]** Definiti operational inainte de implementare: (1) load-bearing cu criteriu testabil; (2) empirical support cu prag numeric; (3) clearly marked for removal cu forma fizica exacta din SKILL.md.
- [ ] **[DEFERRED]** **[AURELIUS]** Reduce apparatus la /consilium parallel sau sequential pentru auditul initial. Ruleaza Senate doar dupa ce auditul produce schimbari concrete acceptate pentru implementare.
- [ ] **[DEFERRED]** **[CONFUCIUS]** Non-blocant: output-ul final sa citeze explicit runs-urile precedente relevante per decizie de eliminare.
- [ ] **[DEFERRED]** **[SOCRATE]** Inainte de a continua, declara: (1) definitia operationala a empirical support; (2) daca recomandari anterioare sunt tratate ca priors acceptati; (3) daca skeptic_on_chosen e evaluat ca flag sau mod peer; (4) criteriul de falsificare.
- [ ] **[DEFERRED]** **[MUSK]** 1. DELETE: dialectic_skeptic + trias_split din SKILL.md. 2. DELETE: scripts/principle_extraction.py. 3. REMOVE: parallel_skeptic ca named mode. 4. DEMOTE: Step 5c la Skill maintenance. 5. COLLAPSE: Step 5d in skeptic_on_chosen auto-trigger. 6. ADD: warning fabricatie Dialectic Pass-2. 7. TIGHTEN: dialectic_merge.py dissent fallback la hard rejection.
- [ ] **[DEFERRED]** **[DIMON]** (1) Mecanism de verificare cross-referinta dupa eliminari. (2) Tratament runs/ istorice cu mode labels eliminate. (3) Exit condition pentru auto-modificare reflexiva senate.

---

## Rollback hooks

- **R.1** Toate vocile noi (philosophical variants) sunt **paralele**, nu înlocuiesc — zero risc dacă nu sunt apelate.
- **R.2** Dacă `aggregator.py` strică runs vechi → revert acel commit, păstrează prompts.
- **R.3** Dacă Senatul mod e prea scump → marcat ca premium, default rămâne standard modes.
- **R.4** Dacă Napoleon over-fitted (post Phase 14A) → retras din Senat, rămâne Senatul de 6.

---

**End of consolidated TODO.**
