# TO_DO Consilium — Sugestii din sesiunile 2026-05-15 + 2026-05-16

Rankate după raportul impact / efort. Categorii: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch** (arhitectură).

**Stare 2026-05-15:** #13, #14, #15, #19 sunt implementate pe branch `feat/feedback-and-quality-loop` (vezi commit). #1, #16, #17, #20 dropped după deliberare Consilium (`runs/2026-05-15_2236_todo-triage.json`, chosen=`minimal_next_ship`, drop unanim între candidate non-trivial pentru #16/17/18/20; #1 drop la cerere user). #9 și #18 sub investigație (user). Restul rămân deschise.

**Stare 2026-05-16:** adăugate #20-#28 din audit-ul vocilor (Trias + parallel-skeptic, `runs/2026-05-16_0148_voice_audit_meta.json`, conf=0.80). Toate sunt deschise; #20 e quick-win HIGH severity (naming collision).

**Follow-up eval parity (planificat după parallel-review 0.57 conf):** branch `feat/eval-parity-rest` cu scenarii pentru:
- `memory.py` tier medium/long/unknown (3 scenarii — cer fixtures runs/)
- `audit_feedback.py` orphan detection + `--backfill` idempotency (2 scenarii — cer fixture FEEDBACK.html + runs/*.json)
- `mark_outcome.py` `[confirmed]` marker preservation (1 scenariu — cere fixture FEEDBACK.html)
- `priors.py` `weighted_bad_rate` + `missing_feedback_runs` + `stale_pendings` cutoff (3 scenarii — cer fixtures)
Total ~9 scenarii noi. Cere extensie a `run_evals.py` să accepte fixtures de filesystem (în prezent doar stdin_json + CLI args).

---

## Tier 1 — Quick wins (impact mare, efort mic)

### 2. Conservator Mindset — "scorezi risc, nu valoare netă"
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic

Acum Conservator poate veta nejustificat o schimbare cu risc 0.7 dar beneficiu enorm. Prompt-ul nu spune că `risk_score` e un semnal pentru aggregator, nu o decizie finală.

Fix: adaugă în Mindset:
```
You score risk, not net value. A high risk_score is a flag for the aggregator,
not a veto. Don't inflate scores to steer the outcome.
```

---

### 3. Control Mindset — standard consistent între candidați
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic

Control poate fi implicit mai strict cu `unconventional_*` pentru că "pare ciudat" și mai indulgent cu abordarea familiară — fără să realizeze că aplică standarde diferite.

Fix: adaugă în Mindset:
```
Apply the same standard to every candidate. Familiarity is not a validity signal.
```

---

### 4. Generator Mindset — nu te ancora pe prima soluție obvioasă
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

Generator poate produce 4 variante ale aceleiași idei cu formulări diferite și tot respectă "Quantity before quality". Lipsă de instrucțiune privind ordinea generării.

Fix: adaugă în Mindset:
```
Think at multiple levels: user-visible behavior, internal mechanism, infrastructure.
Generate the obvious solution last — explore the non-obvious first.
```

---

### 5. ID preservation explicit în toate 3 voci
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

Niciun prompt nu spune că `id`-urile trebuie păstrate verbatim între Generator → Control → Conservator. Un drift de naming face aggregatorul să eșueze silențios.

Fix: adaugă în fiecare `## Output format`:
```
The `id` field must be preserved verbatim from Generator through all voice outputs.
```

---

### 6. Definiție "shared/core code" în Conservator
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

Generator îl definește (`auth/`, `migrations/`, `security/`, public APIs) dar Conservator scorează `scope_drift` fără referință consistentă la aceeași definiție.

Fix: adaugă în `## Input` din `conservator.md`:
```
Core/shared zones (reference for scope_drift): auth/, migrations/, security/,
public APIs, dependency files, .github/workflows/
```

---

### 7. Sketch depth specificat în Generator
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

`sketch` poate fi o linie sau 10 paragrafe — nu există ghidaj. Rezultatul e inconsistent și Control nu poate verifica un sketch prea vag.

Fix: adaugă în Constraints:
```
Sketch depth: 2–5 sentences or pseudocode equivalent.
Show *where* and *how*, not just "change X to Y".
```

---

### 8. Control — instrucțiune explicită pentru citit fișiere
**Categorie:** Prompt | **Impact:** Mediu | **Efort:** Mic

"Access to relevant files if you need to check signatures" e vag. Control speculează în loc să verifice când nu are certitudine.

Fix: adaugă în Mindset sau Task:
```
If you cannot verify a signature without reading a file, read it.
If the file is not accessible, mark: category: "types", detail: "unverifiable — file not accessible".
Never guess and mark it verified.
```

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

## Sumar rapid

| # | Titlu | Categorie | Impact | Efort |
|---|-------|-----------|--------|-------|
| 2 | Conservator: risc ≠ valoare netă | Prompt | Înalt | Mic |
| 3 | Control: standard consistent | Prompt | Înalt | Mic |
| 4 | Generator: nu te ancora | Prompt | Mediu | Mic |
| 5 | ID preservation explicit | Prompt | Mediu | Mic |
| 6 | Shared/core code definit în Conservator | Prompt | Mediu | Mic |
| 7 | Sketch depth specificat | Prompt | Mediu | Mic |
| 8 | Control: citește fișierele, nu specula | Prompt | Mediu | Mic |
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
