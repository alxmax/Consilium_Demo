# Contributing to max-agent

Acest repo este sursa skill-ului `max-agent`. Pentru a-l **folosi**, invocă `/max-agent` într-o sesiune Claude Code. Acest fișier acoperă doar **editarea** skill-ului.

## Contract

`SKILL.md` e contractul public. Citește-l înainte de orice modificare — Constitution (4 principii) și workflow-ul în 6 pași guvernează skill-ul, nu doar utilizatorii lui.

## Convenții Python

- **Stdlib-only.** Niciun script nu introduce dependențe externe. Dacă pare necesar, e probabil semn că feature-ul depășește scope-ul skill-ului.
- **Scripts mici, stand-alone.** Fiecare `scripts/*.py` are docstring CLI, `argparse`, JSON I/O. Reuse între scripts merge prin `importlib.util` (vezi `priors.py`), nu prin packaging.
- **No tests dir.** Smoke-test manual prin CLI; vezi `python scripts/validate_report.py < runs/<latest>.json` ca minim.

## Zone autoritative (atinge cu grijă)

- **`prompts/*.md`** — citite de fiecare voce la rulare. O schimbare aici afectează toate deliberările viitoare → `regression_risk` mare în Conservator. Preferă să injectezi context suplimentar în input-ul vocii, nu în prompt.
- **`SKILL.md` Constitution + workflow** — schimbarea pașilor 1-6 rupe formatul JSON așteptat de `aggregator.py` și `validate_report.py`. Modifică deodată ambele.

## Fișiere locale (gitignored)

- `FEEDBACK.md` — jurnal personal, păstrat pe disc.
- `runs/*.json` — output-urile fiecărei deliberări (păstrate `runs/README.md` ca singur tracked).

## Self-improvement loop

Când editezi skill-ul însuși: rulează `/max-agent` pe propria schimbare. Dacă modul paralel e activat, vocile sunt sub-agenți independenți — dovadă mai puternică decât deliberarea single-context. Salvează run-ul în `runs/` și adaugă o linie în `FEEDBACK.md`.
