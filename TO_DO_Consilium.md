# TO_DO Consilium — Sugestii din sesiunea 2026-05-15

Rankate după raportul impact / efort. Categorii: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch** (arhitectură).

**Stare 2026-05-15:** #13, #14, #15, #19 sunt implementate pe branch `feat/feedback-and-quality-loop` (vezi commit). Restul rămân deschise.

**Follow-up eval parity (planificat după parallel-review 0.57 conf):** branch `feat/eval-parity-rest` cu scenarii pentru:
- `memory.py` tier medium/long/unknown (3 scenarii — cer fixtures runs/)
- `audit_feedback.py` orphan detection + `--backfill` idempotency (2 scenarii — cer fixture FEEDBACK.html + runs/*.json)
- `mark_outcome.py` `[confirmed]` marker preservation (1 scenariu — cere fixture FEEDBACK.html)
- `priors.py` `weighted_bad_rate` + `missing_feedback_runs` + `stale_pendings` cutoff (3 scenarii — cer fixtures)
Total ~9 scenarii noi. Cere extensie a `run_evals.py` să accepte fixtures de filesystem (în prezent doar stdin_json + CLI args).

---

## Tier 1 — Quick wins (impact mare, efort mic)

### 1. `success_criterion` explicit în Input la toate 3 voci
**Categorie:** Prompt | **Impact:** Înalt | **Efort:** Mic

Acum vocile primesc "the user's stated goal" — o formulare liberă. `success_criterion` e propoziția testabilă din Step 1 și e mai precisă. Conservator nu poate scora corect `scope_drift` fără ea.

Fix: adaugă `success_criterion: <string>` ca prim câmp în secțiunea `## Input` din `generator.md`, `control.md`, `conservator.md`.

---

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

### 16. Meta-controller cu autoritate reală
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Mare

Acum orchestratorul execută pașii secvențial fără să poată decide "deliberarea a deraiat, restart cu alt framing". Nu poate sări Control pentru un candidat trivial sau cere mai mult context înainte de Generator.

Implementare: un script `meta_controller.py` care primește starea curentă și decide next step (continue / restart / enrich-context / skip-voice).

---

### 17. Semantic memory — deliberări trecute căutabile prin similaritate
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Foarte Mare

`runs/*.json` sunt episodice dar nu căutabile tematic. `priors.py` citește ultimele N runs indiferent de relevanță. Nu poți întreba "deliberări trecute similare cu această schimbare de auth".

Necesită: indexare embeddings pe `runs/*.json` + query la Step 0 cu schimbarea curentă ca seed.

---

### 18. Observe → Think → Act → Learn loop formal
**Categorie:** Arch | **Impact:** Mediu | **Efort:** Foarte Mare

Schelet-ul există deja implicit (Step 1 = Observe, Steps 2-4 = Think, Step 5 = Act, Step 6 = Learn). Formalizarea ca loop explicit cu state machine ar permite restart, enrichment, și skip-uri condiționate.

Risc: Consilium devine agentic și nedeterminist — contrazice Principiul 2 (Simplicity first). De implementat doar dacă meta-controller (17) e deja stabil.

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

### 20. Mecanism variation example în Generator Constraints
**Categorie:** Prompt | **Impact:** Scăzut | **Efort:** Mic

"Vary on at least one axis: scope, abstraction level, timing, or mechanism" — `mechanism` e cel mai abstract ax și cel mai rar variat în practică pentru că nu există exemplu concret.

Fix: adaugă exemplu inline:
```
mechanism: e.g. instead of patching at call site, intercept at middleware level;
instead of polling, use event-driven notification.
```

---

## Sumar rapid

| # | Titlu | Categorie | Impact | Efort |
|---|-------|-----------|--------|-------|
| 1 | success_criterion în Input la toate 3 | Prompt | Înalt | Mic |
| 2 | Conservator: risc ≠ valoare netă | Prompt | Înalt | Mic |
| 3 | Control: standard consistent | Prompt | Înalt | Mic |
| 4 | Generator: nu te ancora | Prompt | Mediu | Mic |
| 5 | ID preservation explicit | Prompt | Mediu | Mic |
| 6 | Shared/core code definit în Conservator | Prompt | Mediu | Mic |
| 7 | Sketch depth specificat | Prompt | Mediu | Mic |
| 8 | Control: citește fișierele, nu specula | Prompt | Mediu | Mic |
| 9 | Goal-fit → pasul 0 în Control | Prompt | Mediu | Mic-Mediu |
| 10 | Cap stacking regression_risk | Prompt | Mediu | Mic |
| 11 | Candidați ireversibili by nature | Prompt | Mediu | Mediu |
| 12 | probe_change data în Conservator Input | Prompt | Mediu | Mic |
| 13 | Single retry la confidence scăzut | Skill | Mediu | Mediu |
| 14 | Meta-critic calitate deliberare | Arch | Înalt | Mare |
| 15 | Feedback din outcome real | Arch | Înalt | Mare |
| 16 | Meta-controller cu autoritate | Arch | Mediu | Mare |
| 17 | Semantic memory | Arch | Mediu | Foarte Mare |
| 18 | Observe→Think→Act→Learn formal | Arch | Mediu | Foarte Mare |
| 19 | Memory tiers formalizate | Arch | Scăzut | Mare |
| 20 | Mechanism variation example | Prompt | Scăzut | Mic |
