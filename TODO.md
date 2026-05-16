# TODO — consolidat (2026-05-16)

> Consolidare a 3 TODO-uri vechi:
> - `TODO.md` (root) — 5 stale pendings 2026-05-12
> - `experiments/New phase senat/todos/TODO_SENAT.md`
> - `experiments/New phase senat/todos/TODO_RUND2.md`
> - `experiments/New phase senat/todos/TODO-philosophical-voice-variants.md`
>
> Documentul de referință `experiments/New phase senat/todos/SENAT-todo-rol-legi-functii.md` rămâne ca specificație conceptuală (nu e TODO acțional).

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

---

## ❌ NEIMPLEMENTAT

### Philosophical voice variants (PR pending: `feat/philosophical-voice-variants`)

> **Status:** plan + spec doar; niciun cod efectiv.
> Fișiere existente: `docs/superpowers/plans/2026-05-16-philosophical-voice-variants.md`, `docs/superpowers/specs/2026-05-16-consilium-experimental-implementation-design.md`
> **Note critic:** parțial **deja absorbit în RUND2** — Wittgenstein și Aurelius pattern-urile sunt integrate în vocile core. Revizuie scope-ul înainte de implementare.

**Voci de adăugat:**

- [ ] `prompts/control_wittgenstein.md` — semantic verification (`glossary` + `hidden_assumptions`)
  - *Note:* RUND2 deja a injectat `glossary` în `control.md`. Decide dacă mai e nevoie de variantă separată.
- [ ] `prompts/conservator_aurelius.md` — `reversibility × magnitude` matrix
  - *Note:* RUND2 deja a integrat matricea în `conservator.md`. Probabil deprecated.
- [ ] `prompts/control_aurelius.md` — zone-of-control filtering (`in_control`, `out_of_control`, `wasted_deliberation`)
  - *Status:* încă util — nu e absorbit în RUND2
- [ ] `prompts/conservator_confucius.md` (EXPERIMENTAL) — precedent consultation
  - *Note:* parțial implementat prin `scripts/principle_extraction.py`. Decide dacă voce separată mai e necesară.
- [ ] `prompts/refiner_deletion.md` — refinement layer (Musk "make it FAST")
  - *Status:* NU e absorbit, categorie nouă (post-processor după Aggregator)
- [ ] `scripts/precedent_search.py` — pentru Confucius (gating pe >=10 runs/)
- [ ] Phase 5c — internal question audit pentru toate vocile (4 criterii: operațională, discretă, self-scaling, bounded)
- [ ] Phase 7 — patch `validate_report.py` cu `--strict-philosophical=<voice>` flags
- [ ] Phase 8 — tests dedicate (Wittgenstein, Aurelius, Control+Aurelius, Confucius, Refiner)
- [ ] Phase 13 — empirical validation (10-15 întrebări reale)

**Recomandare:** redeschide TODO-ul după ce evaluezi ce s-a absorbit în RUND2. Probabil scope-ul se reduce la `control_aurelius` + `refiner_deletion` + question audit.

---

### Stale pendings 2026-05-12 (din priors.py)

> Cinci entries PEND vechi în `priors.py`, surface după închiderea batch-ului 2026-05-11.
> Toate provin din work-ul pe `docs/architecture.html`.
> **Decizia probabilă:** revisit retroactiv prin `mark_outcome.py` după ce verifici starea finală în repo.

- [ ] **`add_null_confidence_branch`** (2026-05-12) — Context: "docs/architecture.html accurately reflects the confidence-g…". Verifică dacă branch-ul null-confidence a aterizat în diagramă.
- [ ] **`recompute_aggregation_table`** (2026-05-12) — Context: "Diagrams and worked example in docs/architecture.html accur…". Cross-check cu `aggregator.py`.
- [ ] **`drop_f1_keep_f2_f3`** (2026-05-12) — Context: "Identify the smallest-scope intervention…". Verifică edit-urile pe `prompts/generator.md`.
- [ ] **`interp_b_ship_subset_f2_f3_only`** (2026-05-12) — Context: "The 3 prompt edits (F1 unconventional_* mandate in Generato…". Diff vs main.
- [ ] **`ship_f1_only_now`** (2026-05-12) — Context: "After applying 3 prompt edits…". Contradictoriu cu cele de mai sus — care a câștigat?

**Cum se rezolvă fiecare:**
1. Read run JSON-ul corespunzător din `runs/2026-05-12_*.json` (există 10+ rulări din acea zi).
2. Verifică codul curent vs sketch-ul chosen.
3. Dispatch `consilium-subagent` (model adaptat la complexitate) pentru deliberare retroactivă.
4. `python scripts/mark_outcome.py --date 2026-05-12 --chosen <id> --outcome OK|BAD --reason "<rationale>"`.

**Note:** Cele trei alegeri (`drop_f1_keep_f2_f3`, `interp_b_ship_subset_f2_f3_only`, `ship_f1_only_now`) trebuie investigate împreună — par contradictorii. Vezi `git log --since=2026-05-12 --until=2026-05-13`.

---

## 🤔 DECIZII NEREZOLVATE

Din `TODO_RUND2.md` Anexa D — decizii personale care nu blochează implementarea curentă, dar trebuie luate cândva:

- [ ] **Modul paralel rămâne selectabil de user?** Senatul a votat să-l elimini. Dacă ești atașat de mod paralel pentru deliberări rapide, contestă.
- [ ] **Veto budget pentru `meta_recommendation`: 5/lună acceptabil?** Aurelius+Napoleon au propus, dar numărul e arbitrar. Poate vrei 10 sau 3.
- [ ] **Outcome tracking — manual sau automat?** Pentru trading se poate automat din MT4. Pentru altele cere completare manuală. Dacă nu, `principle_extraction` nu se activează niciodată.
- [ ] **Napoleon rămâne senator după empirical validation?** Phase 14B din TODO_RUND2 verifică over-fit la P3. Decide după validare.

Din `TODO_SENAT.md` Anexa D:

- [ ] **Senatori viitori (slot 8 și 9)** — decizi când apar candidați. Reguli: testul P3, specialitate non-overlapping >50%, audit de Senatul existent înainte de adăugare.
- [ ] **Reduci Senat de 7 la 6 dacă pare prea costisitor după 5-10 invocări?**

---

## 📋 POST-MERGE VALIDATION (din TODO_RUND2 Phase 14)

Pendings empirice după merge-ul RUND2 (PR #59 — `2026-05-16`):

- [ ] **14A — Napoleon validation** pe 5-10 întrebări diverse (operaționale + filozofice + ambigue). Verifică over-fit la P3.
- [ ] **14B — Sequential dispatch validation**: rezultă calibrare mai bună decât paralel vechi pe 10 întrebări reale?
- [ ] **14C — Aggregator decisions validation**: pattern detection pe veto-uri în primele 30 runs.
- [ ] **14D — Genereaza `experiments/run4-rund2-empirical-validation.html`**

---

## Rollback hooks (referință)

- **R.1** Toate vocile noi (philosophical variants) sunt **paralele**, nu înlocuiesc — zero risc dacă nu sunt apelate.
- **R.2** Dacă `aggregator.py` strică runs vechi → revert acel commit, păstrează prompts.
- **R.3** Dacă Senatul mod e prea scump → marcat ca premium, default rămâne standard modes.
- **R.4** Dacă Napoleon over-fitted (post Phase 14A) → retras din Senat, rămâne Senatul de 6.

---

**End of consolidated TODO.**
