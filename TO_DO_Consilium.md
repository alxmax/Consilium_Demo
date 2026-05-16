# TO_DO Consilium — Sugestii din sesiunile 2026-05-15 + 2026-05-16

Rankate după raportul impact / efort. Categorii: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch** (arhitectură).

**Stare 2026-05-15:** #13, #14, #15, #19 sunt implementate pe branch `feat/feedback-and-quality-loop` (vezi commit). #1, #16, #17, #20 dropped după deliberare Consilium (`runs/2026-05-15_2236_todo-triage.json`, chosen=`minimal_next_ship`, drop unanim între candidate non-trivial pentru #16/17/18/20; #1 drop la cerere user). #9 și #18 sub investigație (user). Restul rămân deschise.

**Stare 2026-05-16 (audit la finalul Branch 3 sync):** items #2, #3, #4, #5, #6, #7, #8 sunt deja implementate în prompts (descoperite la implementarea planului Branches 1–5; TODO-ul era desincronizat cu codul). Marcate `✅ DONE` cu pointer la file:line.

**Stare 2026-05-16:** adăugate #20-#28 din audit-ul vocilor (Trias + parallel-skeptic, `runs/2026-05-16_0148_voice_audit_meta.json`, conf=0.80). Toate sunt deschise; #20 e quick-win HIGH severity (naming collision).

**Stare 2026-05-16 (audit LangGraph/LangChain):** adăugate #47-#50 din `runs/2026-05-16_1430_audit_langgraph_langchain.json` (chosen=`do_nothing`, conf=0.36 PEND, mode=parallel). Audit-ul a respins integrarea profundă (veto pe full rewrite, invalid pe LangChain output parsers, invalid pe topology-only). #47 e runner-up (sidecar izolat); #48-#50 sunt pattern-uri LangGraph-inspired propuse pentru analiză înainte de orice implementare.

**Stare 2026-05-16 (P3 corrigendum):** adăugate #51-#53 din lecțiile inversării — user a confirmat că răspunsul corect la P3 este C (cu mașina), nu A (pe jos). Toate sintezele inițiale din `experiments/` etichetau eronat C drept "fabricație model-wide"; cu oracle-ul corect, claim-ul se inversează semantic. Vezi `experiments/p3-car-wash.html` (HTML consolidat + corigendum). Cele 3 entry-uri sunt deschise pentru analiză.

**Follow-up eval parity (planificat după parallel-review 0.57 conf):** branch `feat/eval-parity-rest` cu scenarii pentru:
- `memory.py` tier medium/long/unknown (3 scenarii — cer fixtures runs/)
- `audit_feedback.py` orphan detection + `--backfill` idempotency (2 scenarii — cer fixture FEEDBACK.html + runs/*.json)
- `mark_outcome.py` `[confirmed]` marker preservation (1 scenariu — cere fixture FEEDBACK.html)
- `priors.py` `weighted_bad_rate` + `missing_feedback_runs` + `stale_pendings` cutoff (3 scenarii — cer fixtures)
Total ~9 scenarii noi. Cere extensie a `run_evals.py` să accepte fixtures de filesystem (în prezent doar stdin_json + CLI args).

---

## Tier 1 — Quick wins (impact mare, efort mic)

### 2. Conservator Mindset — "scorezi risc, nu valoare netă" ✅ DONE
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic
**Status:** implementat în `prompts/conservator.md:7` ("Risk signal, not decision. You score risk, not net value. A high risk_score is a flag for the aggregator, not a veto. Don't inflate scores to steer the outcome.").

---

### 3. Control Mindset — standard consistent între candidați ✅ DONE
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic
**Status:** implementat în `prompts/control.md:11` ("Consistent standard across candidates. Apply the same scrutiny to every candidate. Familiarity is not a validity signal.").

---

### 4. Generator Mindset — nu te ancora pe prima soluție obvioasă ✅ DONE
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic
**Status:** implementat în `prompts/generator.md:42` ("Multi-level exploration. Think at multiple levels: user-visible behavior, internal mechanism, infrastructure. Generate the obvious solution last — explore the non-obvious first.").

---

### 5. ID preservation explicit în toate 3 voci ✅ DONE
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic
**Status:** implementat în toate 3 prompts — `prompts/generator.md:49`, `prompts/control.md:35`, `prompts/conservator.md:45` ("The `id` field must be preserved verbatim from Generator through all voice outputs.").

---

### 6. Definiție "shared/core code" în Conservator ✅ DONE
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic
**Status:** implementat în `prompts/conservator.md:19` ("Core/shared zones (reference for `scope_drift`): `auth/`, `migrations/`, `security/`, public APIs, dependency files, `.github/workflows/`").

---

### 7. Sketch depth specificat în Generator ✅ DONE
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic
**Status:** implementat în `prompts/generator.md:43` ("Sketch depth: 2–5 sentences or pseudocode equivalent. Show *where* and *how*, not just \"change X to Y\".").

---

### 8. Control — instrucțiune explicită pentru citit fișiere ✅ DONE
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic
**Status:** implementat în `prompts/control.md:9` ("Verify, don't speculate. ... If you cannot verify a signature without reading a file, read it. If the file is not accessible, mark `category: \"types\"`, `detail: \"unverifiable — file not accessible\"`. Never guess and mark it verified.").

---

## Tier 2 — Medii (impact mare, efort mediu)

### 9. Goal-fit check mutat la pasul 1 în Control
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic-Mediu
**Status:** INVESTIGATE (user, 2026-05-15) — re-evaluare înainte de ship.

Acum Control face types → logic → tests → style → goal-fit. Dacă candidatul nu adresează success_criterion, primele 4 verificări sunt irosite.

Fix: mută goal-fit ca **pasul 0** în Task, înainte de types. Fail fast.

---

### 10. Cap pe stacking regression_risk reduction în Conservator
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

Prompt-ul spune `-0.15` pentru test coverage dar nu specifică dacă se aplică și pentru feature flag și rollback < 3 pași simultan. Nedefinit → aplicare inconsistentă.

Fix: adaugă:
```
regression_risk reduction: max cumulative −0.20, regardless of how many
mitigations are present. Document each reduction applied in notes.
```

---

### 11. Handling pentru candidați ireversibili by nature
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mediu

Published API change, migration live — `rollback_recipe` executabil e imposibil. Acum rezultă rollback_recipes false/abstracte.

Fix: adaugă în Conservator Task:
```
If rollback is structurally impossible (published API already consumed by clients,
live migration with data writes), replace rollback_recipe with mitigation_steps
and add "irreversible": true at candidate level.
```

---

### 12. `probe_change.py` data menționată explicit în Conservator Input
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

`probe_change.py` produce `files_changed`, `lines_changed`, `churn` — date concrete pentru `diff_size` și `regression_risk` — dar prompt-ul nu menționează că le poate primi. Le ignoră sau le inventează.

Fix: adaugă în `## Input`:
```
Optional: probe data — files_changed, lines_changed, churn_per_file (last N days).
Use to anchor diff_size and regression_risk when present.
```

---

### 13. Single retry cu context îmbogățit la confidence scăzut ✅ DONE
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mediu
**Status:** implementat în `scripts/retry_context.py` + SKILL.md Step 5d.

Când confidence < 0.7, acum skill-ul întreabă utilizatorul. Un singur retry automat cu context suplimentar specific pentru top 2 candidați ar putea rezolva ambiguitatea fără intervenție umană.

Flow propus:
```
confidence < 0.7
  → identifică top 2 candidați (cei mai apropiați ca scor)
  → gather context specific pentru ei (call sites, test coverage, file owners)
  → re-deliberare o singură dată cu acel context extra
  → dacă tot sub prag → PEND, user decide
```
**Nu** un loop de 10 iterații — un singur retry cu input diferit.

---

## Tier 3 — Arhitecturale (impact înalt, efort mare)

### 14. Meta-critic pe calitatea deliberării ✅ DONE
**Categorie:** Arch | **Impact:** Înalt | **Efort:** Mare
**Status:** implementat în `scripts/meta_critic.py` + SKILL.md Step 5c. Build_report pasează `deliberation_quality` în raport.

`validate_report.py` verifică schema JSON, nu calitatea gândirii. Nu există nimic care să detecteze:
- Generator a produs 4 variante ale aceluiași lucru (divergența e falsă)
- Control nu a verificat nimic concret, a speculat
- Conservator a dat scoruri identice tuturor (0.5 shrug)

Implementare: un pas 5b de meta-critic care rulează pe `bundle.json` înainte de aggregare și emite `deliberation_quality: {generator_divergence, control_concreteness, conservator_spread}`.

---

### 15. Feedback din outcome real (producție → calibrare) ✅ DONE
**Categorie:** Arch | **Impact:** Înalt | **Efort:** Mare
**Status:** implementat în `scripts/mark_outcome.py` (suprascrie outcome retroactiv cu marker `[confirmed]`) + `priors.py` ponderează 2x rândurile confirmate (`weighted_bad_rate`).

`FEEDBACK.html` stochează OK/BAD/OVR dar semnalul vine de la utilizator imediat după deliberare, nu din producție. Nu există mecanism care să închidă loop-ul *"schimbarea aleasă a cauzat un bug în prod → retroactiv BAD."*

Necesită: un CLI `consilium mark-outcome <run-id> BAD --reason "..."` și actualizarea `priors.py` să pondereze mai greu BAD-urile cu outcome confirmat față de cele subiective.

---

### 18. Observe → Think → Act → Learn loop formal
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Foarte Mare
**Status:** INVESTIGATE (user, 2026-05-15) — păstrat pentru explorare ulterioară.

Schelet-ul există deja implicit (Step 1 = Observe, Steps 2-4 = Think, Step 5 = Act, Step 6 = Learn). Formalizarea ca loop explicit cu state machine ar permite restart, enrichment, și skip-uri condiționate.

Risc: Consilium devine agentic și nedeterminist — contrazice Principiul 2 (Simplicity first). De implementat doar dacă meta-controller (16, dropped) e deja stabil.

---

### 19. Short / Medium / Long-term memory formalizate explicit ✅ DONE

**Categorie:** Arch | **Impact:** Scăzut | **Efort:** Mare
**Status:** documentat în SKILL.md secțiunea "Memory tiers" + `scripts/memory.py` ca read API uniform peste cele 3 layere.

Memoria există deja în 3 straturi informale:
- **Short**: context window al deliberării curente
- **Medium**: `runs/*.json` (episodic)
- **Long**: `FEEDBACK.html` + `priors.py`

Formalizarea nu adaugă capabilități noi — doar documentație și posibil un API uniform pentru citire/scriere. Valoros doar dacă semantic memory (18) e implementată și necesită un layer comun.

---

## Sugestii din sesiunea 2026-05-16 — audit voci (Trias + parallel-skeptic)

Sursa: `runs/2026-05-16_0148_voice_audit_meta.json` (sinteză 2 subagenți). Trias 3-0 unanimous + parallel-skeptic confirmă core findings. Detalii per voce + evidence în raport.

### 20. Skeptic naming collision — rename `Conservator — Skeptical Voice` → `Risk Assessor`
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic

`conservator.md:1` se autotitrează "Skeptical Voice" dar voca scorează risc, nu correctness. Real-skeptic-ul (uncharitable reading) trăiește în slot-ul `adversarial_*` din Generator (`generator.md:31-37`). Onboarding hazard real — developerul mapează "Skeptic" → Conservator din titlu și se înșeală despre rol.

Fix:
```
# conservator.md:1
# Conservator — Risk Assessor

# + în Mindset:
Skepticism about correctness is Control's job;
skepticism about scope and reversibility is yours.
```

Renaming global la `Skeptic` respins (47 runs în priors + ~12 touchpoints — schema migration).

---

### 21. Fix `meta_critic.conservator_spread` denominator (range-relative)
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`meta_critic.py:82` rescalează `pstdev` prin `MAX_RISK_STDEV = 0.5` (max teoretic bimodal {0,1}). Spread genuin de 0.2/0.3/0.4 produce `pstdev≈0.082`, rescalat 0.164 — flag-uit "weak" deși Conservator a făcut treabă reală.

Fix: `stdev / max(max_risk - min_risk, 0.5)`, fallback la 0.5 doar când `range < 0.2` (single-cluster, shrug real).

---

### 22. Fix `meta_critic.control_concreteness` — interzice fallback-ul 40-char
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`meta_critic.py:74-80,139` admite un detail ≥40 chars ca "concret" indiferent de conținut. *"this approach might have some edge cases that are difficult to handle properly"* (70 chars, zero specifice) trece testul.

Fix: cere file/symbol regex match SAU technical claim specific — definit ca o referință în backticks (symbol/error class), număr de linie, sau condiție explicită ("when X is empty", "on null input").

---

### 23. Codifică formula Conservator `risk_score` în prompt
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

`conservator.md:36` descrie regula reversibility-dominance în proză; implementarea efectivă trăiește în `aggregator.py`. LLM-ul Conservator computează un `risk_score` care poate să nu se potrivească cu cel din aggregator pentru aceleași inputs — single source of truth lipsă.

Fix: code block în prompt:
```
risk_score = mean(diff_size, scope_drift, regression_risk, reversibility)
if reversibility > 0.7:
    risk_score = max(risk_score, reversibility)
```

---

### 24. Rebalance Architect lens — `conservator 0.21→0.30, control 0.49→0.40`
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`personalities.py:24,29`: atât Pioneer cât și Architect au `conservator=0.21`. În coaliția 2-1 cea mai comună (Pioneer+Architect win, Steward dissents), weight-ul efectiv pe Conservator e 0.21 — **sub** baseline-ul echi-ponderat de 0.33. Bias structural spre subponderarea riscului.

Fix:
```python
# personalities.py:29 (Architect)
{"generator": 0.30, "control": 0.40, "conservator": 0.30}
```
Architect rămâne correctness-dominant; safety capătă ballast real.

---

### 25. `meta_critic.py --strict` default când `mode=trias`
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`meta_critic.py:214-233`: `--strict` enables CI exit-1 dar nu e cablat la nicio configurație. În rularile high-stakes (Trias = 9 sub-agenți, costos), drift-ul către paraphrasing/speculation e exact ce trebuie prins.

Fix: detectează `mode=trias` în input și aplică `--strict` automat; advisory rămâne default pentru parallel/sequential.

---

### 26. Lărgește trigger adversarial Generator — adaugă semnal hot-path/many-caller
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

`generator.md:31-35`: trigger pentru `adversarial_*` se aprinde doar la (a) clarity gate 2+ interpretări, sau (b) shared/core code. Excluse: performance-critical paths, latency-sensitive code, third-party integrations — exact codul unde uncharitable reading e cea mai valoroasă.

Fix: adaugă trigger (c):
```
(c) the change touches a function with >3 external callers
    or is on a documented hot path
```
Detectabil din `probe_change.py --churn` în bundle context.

---

### 27. Câmp `confidence_in_verdict` în Control + flag meta_critic
**Categorie:** Prompt + Skill | **Impact:** Scăzut | **Efort:** Mediu

`control.md:9` cere "verify, don't speculate" dar Control primește doar sketches, nu cod real. Speculația trece silent — nu există detection path.

Fix: adaugă `confidence_in_verdict: high|medium|low` în schema verdictului; meta_critic flag-uiește orice `valid:true + confidence_in_verdict:low` ca warning în `control_concreteness`. Forțează Control să admită când nu poate verifica.

---

### 28. Metrici noi în meta_critic — `pass2_revision_quality` + `personalities_divergence`
**Categorie:** Skill | **Impact:** Scăzut | **Efort:** Mediu

Două gap-uri în meta_critic.py:
- Nu auditează dialectic Pass-2 — `peer_evidence` poate fi boilerplate ("Control validated this candidate, no changes needed") și trece neobservat.
- Nu măsoară dacă lentilele Trias produc efectiv divergență; dacă toate 3 personalitățile aleg același candidat, lentilele n-au schimbat nimic.

Fix:
- `pass2_revision_quality`: cere `peer_evidence` >20 chars și non-match cu lista boilerplate (`["no change needed", "validated by control", "conservator confirmed"]`).
- `personalities_divergence` (Trias-only): flag advisory când toate 3 personalități converg pe același candidat.

---

## Sugestii din sesiunea 2026-05-16 — audit flow models (Sequential / Parallel / Dialectic / Trias + 5 SPEC moduri)

Findings din auditul peste cele 4 moduri implementate + cele descrise în `docs/architecture.html`. Cu `feat/skeptic-modes` (PR #34) merged, Skeptic + trias_split sunt documentate ca moduri "conceptuale" (SKILL.md). Iterative Dialectic rămâne SPEC nereimplementat.

**Top 3 fixed pe `fix/audit-flow-modes-top3` (#36, #37, #38).** Restul rămân deschise.

### 29. Pass-2 schema obligatorie documentată în SKILL.md
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`dialectic_merge._is_dissent_compliant` cere `revision` SAU `maintained` pe fiecare item Pass-2. SKILL.md secțiunea Dialectic nu menționează contractul. Sub-agent uită câmpul → fallback tăcut la Pass-1.

Fix: documentat parțial în secțiunea Dialectic (commit `3d59f39`). Mai trebuie extins per voce (generator/control/conservator pass2 prompts).

### 30. Failure-mode section în SKILL.md Parallel
**Categorie:** Skill | **Impact:** Înalt | **Efort:** Mic

Sub-agent crash / JSON malformed / timeout nu au recovery path documentat. Cel mai frecvent failure mode în producție.

### 31. VOTE_PATTERN_CONFIDENCE ordonare contraintuitivă
**Categorie:** Skill | **Impact:** Mic | **Efort:** Mic

`2-0` (veto total dintr-o personalitate) primește 0.75 confidence, `2-1` (dissent activ) primește 0.70. Veto e semnal mai grav decât dissent — ordinea trebuie inversată sau justificată. (Parțial atenuat de #37 când dissenter-ul e Steward.)

### 32. Deduplică _TRIAS_EXPECTED_NAMES
**Categorie:** Skill | **Impact:** Mic | **Efort:** Mic

`validate_report.py:161` și `personalities.py:21-37` duplică lista personalităților. Drift inevitabil când adaugi a 4-a.

Fix: import din `personalities.NAMES`.

### 33. Documentează că `strip_context.py` se skip-uiește în Parallel
**Categorie:** Skill | **Impact:** Mic | **Efort:** Trivial

SKILL.md Step 3-4 zice "Sequential: rulează `strip_context.py`" fără să clarifice că Parallel nu are nevoie (sub-agenții sunt deja izolați).

### 34. Şterge sau wrap deprecated `aggregate_weighted`
**Categorie:** Skill | **Impact:** Mic | **Efort:** Mic

`aggregator.py:73` are `aggregate_weighted` cu doar `warnings.warn`. Scoate-l din `SCHEMES` map sau ridică-l la `DeprecationWarning` cu `simplefilter("default")`.

### 35. Folosește issue severity în `_voice_score_from_verdict`
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`dialectic_merge.py:88` și `build_report.py:70` scad 0.15 per issue indiferent de severity. 1 typo trivial = 1 SQL injection. Control prompt cere severity dar score nu o folosește.

Fix: ponderare `0.05 / 0.15 / 0.30` pe `severity: low/medium/high`.

### 36. ✅ Trias telemetry obligatoriu — DONE (`fix/audit-flow-modes-top3`)
**Categorie:** Skill | **Impact:** Înalt | **Efort:** Mic

`validate_report.py:235` exempta Trias de la telemetry, deşi Trias e modul cel mai scump (9 sub-agenți). `usage.py` nu putea roll-ui costuri pentru exact tipul de run unde costul contează cel mai mult. Fix: scoate `if not is_trias` din `_validate_telemetry_required`.

### 37. ✅ Steward-aware vote_pattern confidence — DONE (`fix/audit-flow-modes-top3`)
**Categorie:** Skill | **Impact:** Înalt | **Efort:** Mediu

`confidence_from_vote_pattern` primea doar pattern-ul, ignorând care personalitate a dissent-it / abținut. Steward dissent (vocea conservatoare) și Pioneer dissent (vocea progresistă) erau tratate identic — deşi spec-ul afirmă "Steward abstain semantics: semnal mai puternic". Fix: confidence cade cu 0.1 când Steward e dissenter, 0.15 când abstainer.

### 38. ✅ Pass-2 silent fallback warning — DONE (`fix/audit-flow-modes-top3`)
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mic

`dialectic_merge.py` urmărea `dissent_fallbacks` și `silently_dropped` dar nu warning-uia. Fix: stderr warning când oricare e non-empty. Schema obligatorie documentată în SKILL.md secțiunea Dialectic.

### 39. scope_gate blocklist extends pentru `*secrets*` folder
**Categorie:** Skill | **Impact:** Mic | **Efort:** Trivial

`**/secrets*` matchează `secrets.json` dar nu `with-secrets/foo`. Adaugă `**/*secrets*` sau directorul matching.

### 40. telemetry.voices empty în Parallel → eroare (nu warning)
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Trivial

`validate_report.py:146-154` doar emite warning. Orchestrator parallel care uită să captureze telemetry trece gate-ul, dar `usage.py` skip-uiește runul → cost vizibil 0.

### 41. Tie-break determinist la `team_vote` duplicate top
**Categorie:** Skill | **Impact:** Mic | **Efort:** Trivial

`aggregator.py:277-280` foloseşte `for ... break` pe dict — non-deterministic dacă tally are 2 candidați cu același top count (matematic imposibil cu 3 voturi, dar codul nu validează input). Adaugă `raise ValueError` explicit.

### 42. `signals.files_changed = None` la `CONSILIUM_FORCE_FULL=1` type-safe
**Categorie:** Skill | **Impact:** Mic | **Efort:** Trivial

`scope_gate.py:212-213` emite `None` pentru numerics. Consumeri downstream tipați se sparg. Fix: emite `-1` sau omite câmpurile.

### 43. Iterative Dialectic — SPEC fără implementare
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mare

`docs/architecture.html` descrie modul iterative cu N=1..3 runde + convergence stop, marcat `SPEC` + warning "nu e încă implementat". `dialectic_merge.py` acceptă strict `{pass1, pass2}`.

Fix path: ori implementează schema `{rounds: [...]}` în dialectic_merge.py cu convergence detection, ori șterge modul din HTML și actualizează CLAUDE.md (acum doar Skeptic+trias_split rămân ca "conceptuale, fără cod dedicat").

### 44. Sequential "Chinese wall" iluzoriu — clarify în docs
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mic

Sequential rulează același LLM care joacă 3 roluri în acelaşi context. `strip_context.py` doar curăță prompt-ul vocii următoare; weights interne au procesat deja tot. Nu e Chinese wall real. HTML zice corect "Contaminare redusă" dar utilizatorii probabil interpretează vizualul (`<div class="wall">`) ca izolare reală.

Fix: nota explicită în HTML + SKILL.md că Sequential e single-context, doar prompt-stripped.

### 45. Lens injection validation end-to-end
**Categorie:** Skill | **Impact:** Mediu | **Efort:** Mediu

`prompts/<personality>_lens.md` sunt fişiere arbitrare. Niciun test că Pioneer e progress-leaning vs Steward risk-averse. Editor poate inversa accidental fără să fie detectat — toate testele scriptice trec. Overlap parțial cu #37 (Architect rebalance).

Fix: scenariu eval care rulează un diff cu trade-off conservator-vs-progress și verifică că Pioneer alege novel iar Steward alege baseline.

### 46. Generator Pass-2 candidate diff semantic în `revision_log`
**Categorie:** Skill | **Impact:** Mic | **Efort:** Mediu

`dialectic_merge._diff_candidates` listează `fields: ["sketch", "summary"]` ca "modified" dar nu emite diff propriu-zis. Audit promis ("revision_log auditează ce s-a schimbat") e doar nominal — nu poți reconstrui ce s-a schimbat fără ambele payload-uri originale.

Fix: include payload before/after per field în `revision_log.diffs` (atenție la PII / cost storage).

## Sugestii din sesiunea 2026-05-16 — audit LangGraph/LangChain integration

Sursa: `runs/2026-05-16_1430_audit_langgraph_langchain.json` (parallel mode, 5 candidates, chosen=`do_nothing` conf=0.36 PEND). Auditul a respins integrarea profundă: veto pe full rewrite (risk 0.95), invalid pe LangChain output parsers (interface mismatch + stdlib break), invalid pe topology-only (nu răspunde adopt/reject). Runner-up `optional_sidecar_visualizer` (score 0.800 vs `do_nothing` 0.833, separation 0.033) e singura formă de integrare validă tehnic — tracked ca #47. Pattern-urile #48-#50 sunt împrumutabile din LangGraph fără să adopți biblioteca, dar necesită analiză înainte de orice ship.

### 47. `optional_sidecar_visualizer` — `experiments/langgraph_replay/` izolat
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mediu
**Status:** PROPOSED (runner-up în audit, score 0.800).

Sidecar opțional care vizualizează `runs/*.json` post-hoc. Niciun rol în deliberarea live, niciun import din `scripts/`, venv izolat. Doar dacă apare nevoia reală de vizualizare/replay — altfel rămâne pe lista PROPOSED.

Contracte obligatorii înainte de ship:
1. `experiments/langgraph_replay/` rămâne gitignored sau explicit marcat "not part of the skill"
2. `grep -r 'from scripts\|import scripts' experiments/` returnează zero matches; reciproc, niciun `scripts/*.py` nu importă din `experiments/`
3. `replay.py` output schema definită: Mermaid (`graph TD` sau `stateDiagram`) cu cel puțin un nod per step din `deliberation_log` al run-ului citit

Acceptance tests (din audit, Control voice):
- `replay_reads_existing_run`: `python experiments/langgraph_replay/replay.py --input runs/<id>.json` exit 0, stdout Mermaid valid
- `replay_does_not_import_scripts`: grep clean pe `experiments/`
- `core_scripts_unmodified`: `git diff HEAD -- scripts/` zero changes

Risc principal (Conservator, score 0.30): "optional" devine load-bearing peste timp. Dacă alegem să implementăm, adăugăm guard în CI: blocăm orice PR care adaugă import din `experiments/` în `scripts/`.

---

### 48. Analiză: checkpoint per-step între voci
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mediu
**Status:** INVESTIGATE — pattern LangGraph-inspired, necesită analiză.

Acum `runs/<id>.json` se scrie o singură dată la Step 6 (raport final). Dacă Generator reușește dar Control crash-uiește, pierdem tot output-ul Generator-ului — re-rulez de la zero.

Întrebare de explorat:
- Scriem un partial `runs/<id>_partial.json` după fiecare voce (Generator → după Generator; Control → după Control)? Sau un fișier separat per voce (`runs/<id>/generator.json`, `runs/<id>/control.json`)?
- Cum interacționează cu `audit_feedback.py` (care detectează orphan runs pe glob `runs/*.json`)? Schema directory pe run sau filename-suffix?
- Cost/beneficiu real: cât de des Control/Conservator eșuează vs cât de des ne afectează? Verifică `feedback.py --recent 50` și caută BAD/OVR cauzate de re-run.

Decizie blocată până avem datele. Nu implementa fără audit prealabil.

---

### 49. Analiză: streaming / human-in-the-loop între Generator și Control
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mare
**Status:** INVESTIGATE — pattern LangGraph-inspired, necesită analiză + posibil suport Claude Code.

Acum Generator → Control e automat. Pattern propus: după Generator, pause; orchestratorul afișează candidates și permite utilizatorului să excludă/edite candidate înainte ca Control + Conservator să le vadă.

Întrebare de explorat:
- Există în Claude Code un mecanism nativ de pause + user input între sub-agent calls? Sau trebuie implementat în orchestrator (orchestratorul în two turns explicit, prima emite candidates pentru user)?
- Cum se loghează intervenția? `runs/*.json` are nevoie de un câmp `human_intervention: {step: "post_generator", action: "removed_candidate", id: "..."}` ca să nu poluăm signalul de eval.
- Conflict cu Principle 1 (Think before coding): dacă utilizatorul filtrează candidates, tradeoff-urile vizibile în deliberare se restrâng — riscăm să trecem peste explorări utile.

Decizie blocată până cunoaștem disponibilitatea pause/resume în Claude Code. De preferat: contactează #claude-code dacă există spec, nu construi pe presupuneri.

---

### 50. Analiză: time-travel peste `runs/*.json`
**Categorie:** Skill | **Impact:** Mic | **Efort:** Mic-Mediu
**Status:** INVESTIGATE — pattern LangGraph-inspired, util la debugging eval-uri.

Acum `runs/*.json` sunt immutable după scriere. Pattern propus: un script `scripts/replay_aggregator.py` care citește un run, permite editarea manuală a scorurilor per voce (de exemplu, "ce-ar fi dacă Conservator dădea 0.5 în loc de 0.72?"), și re-rulează aggregator + confidence pe scorurile editate — fără să modifice run-ul original.

Întrebare de explorat:
- Output: nou run (`runs/<id>_replay_<timestamp>.json`) sau JSON pe stdout fără persistare? Persistarea poluează priors; stdout pierde context. Probabil stdout cu flag opțional `--save`.
- Cum interacționează cu `validate_report.py`? Replay-ul nu are voci noi — telemetry rămâne din original sau marker `replay: true`?
- Caz de utilizare real: util când editezi `aggregator.py` și vrei să verifici că noul scheme nu sparge alegerea pe runs vechi (cuplaj util cu `run_evals.py`).

Decizie soft-pozitivă, dar prioritate scăzută. Implementăm dacă apare o eval-iteration session care ar beneficia. Altfel rămâne pe lista PROPOSED.

---

## Lecții din P3 corrigendum (2026-05-16)

Sursa: `experiments/p3-car-wash.html` (HTML consolidat din run1/run2/run3 + corigendum). User a confirmat pe 2026-05-16 că răspunsul corect la P3 este C (pentru a-ți spăla mașina, mașina trebuie să fie la spălătorie). Toate sintezele inițiale erau inversate semantic — ce numeam "fabricație model-wide" era de fapt prinderea constraint-ului real. Memorie: `memory/project_p3_correct_answer.md`.

### 51. Skeptic-on-chosen ca pas opțional după orice mod ✅ DONE
**Categorie:** Skill | **Impact:** Înalt | **Efort:** Mediu
**Status:** ✅ DONE (2026-05-16, branch `feat/skeptic-on-chosen`) — documented as conceptual mode in SKILL.md (analog cu parallel_skeptic / dialectic_skeptic / trias_split). Design decisions encoded: hybrid trigger (flag + auto on conf∈[0.5,0.7]), advisory-by-default with --skeptic-can-override opt-in.

chosen_confirmation_pass = singurul mod cu catch-rate 100% în sim și 4/7 în reruns reale pe P3. Mecanism: o singură voce skeptic pe `chosen` după Pass-1 obligă re-citirea problemei și prinderea constraint-urilor implicite.

Propunere: flag `--skeptic-on-chosen` care rulează 1 voce skeptic după Pass-1 al oricărui mod (Sequential/Parallel/Dialectic/Trias). Cost: +1 voce. Beneficiu: prinde constraint-uri ratate de toate vocile.

Întrebări deschise pentru analiză:
- Trigger automat (la `confidence < threshold` din aggregator) sau opt-in via flag?
- Skeptic-ul **override** pe chosen dacă produce evidence concrete, sau doar advisory în report cu flag `skeptic_caught_constraint: true`?
- Cum se reconciliază cu modul `parallel_skeptic` deja documentat? `parallel_skeptic` rulează skeptic în paralel cu Pass-1 (4 sub-agenți total); propunerea aici e secvențial pe `chosen` — semnal diferit, prompt diferit.
- Risc fals-pozitiv: skeptic-ul pe răspuns ales poate inversa decizii corecte dacă găsește un eșec ipotetic care nu se aplică problemei. Necesită prompt care să distingă "constraint nerezolvat" de "exception case".

---

### 52. ✅ DONE Revizuiește descrierile "Haiku verifiers = anti-fabrication"
**Categorie:** Docs (Skill/Arch HTML) | **Impact:** Mediu | **Efort:** Mic
**Status:** ✅ DONE (2026-05-16, branch `fix/haiku-antifab-claim`) — CLAUDE.md / SKILL.md (Trias split-model) / docs/architecture.html revised with conditional framing.

Rapoartele inițiale din `experiments/run2-p3-reruns.html` (acum comasat în `p3-car-wash.html`) și posibil `docs/architecture.html` + SKILL.md descriu lite_trias_B / synod_split cu claim-ul că Haiku verifiers funcționează ca "anti-fabrication brake".

Corigendum-ul P3 inversează: Haiku e prea shallow pentru a interoga constraint implicit, deci confirmă răspunsul evident — nu e brake, e amplifier de shallow-failure pe probleme cu constraint implicit.

Acțiune:
- Audit grep pe "anti-fabrication", "Haiku verif", "anti-fabricație" în `docs/`, `SKILL.md`, `experiments/`
- Mark-uire condițională: "anti-noise pe probleme triviale fără constraint implicit; anti-catch pe probleme cu constraint implicit"
- SAU eliminare a claim-ului dacă diferențierea pe tipul de problemă e prea fragilă la documentare

---

### 53. Methodologie: oracle verification înainte de orice claim de "fab-rate" ✅ DONE
**Categorie:** Arch (process) | **Impact:** Înalt | **Efort:** Mic
**Status:** ✅ DONE (2026-05-16, branch `fix/oracle-verification-discipline`) — SKILL.md "Skill maintenance → Benchmarking discipline" + `experiments/README.md` (checklist operațional).

Experimentul P3 a etichetat C drept fabricație pe baza quick-take-ului evaluatorului. Oracle-ul a fost greșit → toată concluzia s-a inversat. Risc identic pe P1 (date refactor) și P2 (auth) dacă evaluatorul are quick-take preferat fără oracle independent.

Acțiune: adaugă disciplină de benchmarking — orice claim de tip "fab-rate" / "accuracy" / "catch-rate" trebuie să citeze:
- **Oracle independent**: al doilea expert SAU ground truth verificabil cu citation explicită (linkuri la specs, citate din enunț care fixează constraint-ul, etc.)
- **Critique adverbial**: pentru fiecare răspuns (A/B/C/D), documentează "există o citire alternativă a problemei în care răspunsul X devine corect?" — răspuns explicit per opțiune înainte de a rula benchmark-ul
- **Verdict-ul "fabricație" blocat până la oracle review** — dacă evaluatorul vrea să eticheteze reasoning ca fabricat, trebuie să justifice oracle-ul separat de propria intuiție

Quick-take-ul evaluatorului ≠ oracle. Această disciplină se aplică retroactiv: revizuiește orice fab-rate claim existent în `experiments/` și `runs/` cu această grilă.

---

## Sumar rapid

| # | Titlu | Categorie | Impact | Efort |
|---|-------|-----------|--------|-------|
| 2 | Conservator: risc ≠ valoare netă ✅ DONE (conservator.md:7) | Prompt | Înalt | Mic |
| 3 | Control: standard consistent ✅ DONE (control.md:11) | Prompt | Înalt | Mic |
| 4 | Generator: nu te ancora ✅ DONE (generator.md:42) | Prompt | Mediu | Mic |
| 5 | ID preservation explicit ✅ DONE (3 prompts) | Prompt | Mediu | Mic |
| 6 | Shared/core code definit în Conservator ✅ DONE (conservator.md:19) | Prompt | Mediu | Mic |
| 7 | Sketch depth specificat ✅ DONE (generator.md:43) | Prompt | Mediu | Mic |
| 8 | Control: citește fișierele, nu specula ✅ DONE (control.md:9) | Prompt | Mediu | Mic |
| 9 | Goal-fit → pasul 0 în Control (INVESTIGATE) | Prompt | Mediu | Mic-Mediu |
| 10 | Cap stacking regression_risk | Prompt | Mediu | Mic |
| 11 | Candidați ireversibili by nature | Prompt | Mediu | Mediu |
| 12 | probe_change data în Conservator Input | Prompt | Mediu | Mic |
| 13 | Single retry la confidence scăzut (DONE) | Skill | Mediu | Mediu |
| 14 | Meta-critic calitate deliberare (DONE) | Arch | Înalt | Mare |
| 15 | Feedback din outcome real (DONE) | Arch | Înalt | Mare |
| 18 | Observe→Think→Act→Learn formal (INVESTIGATE) | Arch | Mediu | Foarte Mare |
| 19 | Memory tiers formalizate (DONE) | Arch | Scăzut | Mare |
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
| 36 | Trias telemetry required (DONE) | Skill | Înalt | Mic |
| 37 | Steward-aware confidence (DONE) | Skill | Înalt | Mediu |
| 38 | Pass-2 silent fallback warning (DONE) | Skill | Mediu | Mic |
| 39 | scope_gate blocklist `*secrets*` folder | Skill | Mic | Trivial |
| 40 | Parallel telemetry empty → eroare | Skill | Mediu | Trivial |
| 41 | team_vote tie-break determinist | Skill | Mic | Trivial |
| 42 | scope_gate None signals type-safe | Skill | Mic | Trivial |
| 43 | Iterative Dialectic — SPEC fără implementare | Arch | Mediu | Mare |
| 44 | Sequential Chinese wall — clarify docs | Arch | Mediu | Mic |
| 45 | Lens injection validation end-to-end | Skill | Mediu | Mediu |
| 46 | Pass-2 diff semantic în revision_log | Skill | Mic | Mediu |
| 47 | `optional_sidecar_visualizer` — experiments/ izolat (PROPOSED) | Arch | Mediu | Mediu |
| 48 | Analiză: checkpoint per-step între voci (INVESTIGATE) | Arch | Mediu | Mediu |
| 49 | Analiză: streaming / HITL Generator↔Control (INVESTIGATE) | Arch | Mediu | Mare |
| 50 | Analiză: time-travel peste runs/ (INVESTIGATE) | Skill | Mic | Mic-Mediu |
| 51 | Skeptic-on-chosen ca pas opțional (P3 lesson) ✅ DONE | Skill | Înalt | Mediu |
| 52 | Revizuiește "Haiku = anti-fabrication" în docs (P3 lesson) ✅ DONE | Docs | Mediu | Mic |
| 53 | Oracle verification pe fab-rate claims (P3 lesson) ✅ DONE (SKILL.md + experiments/README.md) | Arch | Înalt | Mic |
