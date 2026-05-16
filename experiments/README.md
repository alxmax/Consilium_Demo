# Experiments — Benchmarking Discipline

Folderul ține rapoarte HTML din runs experimentale ale skill-ului (e.g. `p3-car-wash.html`).

## Înainte de a publica orice fab-rate / accuracy / catch-rate

Disciplină de benchmarking pentru a evita inversări semantice ulterioare (vezi corigendum-ul P3 din `p3-car-wash.html`):

- [ ] **Oracle independent.** Răspunsul corect e fixat prin (a) un al doilea expert care nu a văzut quick-take-ul evaluatorului, SAU (b) citation explicită din enunț/specs care reduce ambiguitatea sub un prag clar. Quick-take-ul evaluatorului ≠ oracle.
- [ ] **Critique adverbial per opțiune.** Pentru fiecare răspuns plauzibil (A/B/C/D...), documentează explicit înainte de a rula benchmark-ul: *"există o citire alternativă a problemei în care răspunsul X devine corect?"*. Răspunsul "nu" trebuie justificat, nu presupus tacit. Acest pas a fost cel ratat pe P3.
- [ ] **Verdict "fabricație" blocat.** Eticheta `fabrication` pe un raționament cere justificarea oracle-ului independent de intuiția evaluatorului. Dacă oracle-ul nu poate fi numit separat, "fabrication" devine "disagree-with-evaluator" și pierde forța de claim cantitativ.

## Audit retroactiv

Orice fab-rate / catch-rate / accuracy publicat anterior se revizuiește prin grila de mai sus. Risc activ identificat 2026-05-16 (P3 corrigendum):

- **P3** — `p3-car-wash.html` are corigendum-ul deja prezent (oracle inversat de la A la C).
- **P1** (date refactor) — neauditat.
- **P2** (auth) — neauditat.

## Format raport

Fișierele HTML din folder sunt consolidate per problemă (e.g. `p3-car-wash.html` agregă run1/run2/run3 + corigendum într-un singur document). Schema neformalizată; conținut minim recomandat:

- enunț (cu citation explicită a constraint-urilor)
- oracle (cum a fost stabilit + de cine)
- per-mode result (mode, chosen, confidence, vote pattern unde aplicabil)
- comentariu / corigendum atunci când rezultatele s-au inversat

Cross-reference: SKILL.md → "Skill maintenance → Benchmarking discipline".
