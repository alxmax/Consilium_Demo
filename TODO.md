# TODO — stale PEND-uri 2026-05-12

Cinci entries PEND vechi (surface din `priors.py` după ce am închis batch-ul 2026-05-11). Toate provin din work-ul pe `docs/architecture.html`. **Analizeaza** fiecare:

- [ ] **`add_null_confidence_branch`** (2026-05-12) — Context: "docs/architecture.html accurately reflects the confidence-g…". Analizeaza: a aterizat branch-ul null-confidence în diagrama din architecture.html? Verifica codul curent + run JSON-ul asociat.

- [ ] **`recompute_aggregation_table`** (2026-05-12) — Context: "Diagrams and worked example in docs/architecture.html accur…". Analizeaza: tabela de agregare a fost recalculata corect? Cross-check cu output-ul `aggregator.py`.

- [ ] **`drop_f1_keep_f2_f3`** (2026-05-12) — Context: "Identify the smallest-scope intervention that meaningfully…". Analizeaza: F1 a fost drop-uit, F2+F3 au fost păstrate? Verifica edit-urile pe `prompts/generator.md`.

- [ ] **`interp_b_ship_subset_f2_f3_only`** (2026-05-12) — Context: "The 3 prompt edits (F1 unconventional_* mandate in Generato…". Analizeaza: interpretarea B (subset F2+F3) a fost ship-uită? Diff vs main pentru a confirma scope-ul final.

- [ ] **`ship_f1_only_now`** (2026-05-12) — Context: "After applying 3 prompt edits to Consilium (unconventional_…". Analizeaza: pare contradictoriu cu `drop_f1_keep_f2_f3` și `interp_b_ship_subset_f2_f3_only` (3 chosen-uri logate aceeasi zi, alegeri incompatibile). Care a câștigat în realitate? Read run JSON-uri din `runs/2026-05-12_*` pentru a reconcilia.

## Cum se rezolva fiecare

Pentru fiecare item:
1. Read run JSON-ul corespunzator din `runs/2026-05-12_*.json` (dacă există).
2. Verifica codul curent vs sketch-ul chosen.
3. Dispatch `consilium-subagent` (model adaptat la complexitate) pentru deliberare retroactiva.
4. `python scripts/mark_outcome.py --date 2026-05-12 --chosen <id> --outcome OK|BAD --reason "<rationale>"`.

## Note

Cele trei alegeri (`drop_f1_keep_f2_f3`, `interp_b_ship_subset_f2_f3_only`, `ship_f1_only_now`) trebuie investigate împreuna — par contradictorii și probabil reflecta deliberari succesive care s-au răzgândit. Vezi `git log --since=2026-05-12 --until=2026-05-13` pentru a vedea ce a aterizat efectiv.
