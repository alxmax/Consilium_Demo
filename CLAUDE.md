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

## Git workflow

Reguli pentru orice schimbare non-trivială făcută de Claude în acest repo:

1. **Branch nou de la `main`** înainte de a edita. Naming: `feat/<slug>` pentru feature-uri / capabilități noi, `fix/<slug>` pentru bugfix-uri. Slug în kebab-case, descriptiv (ex. `feat/parallel-voices`, `fix/aggregator-null-confidence`). Doar aceste două prefix-e.
2. **Un singur commit per branch** — primul `git commit`, apoi `git commit --amend --no-edit` (sau cu mesaj nou dacă scope-ul s-a schimbat) la fiecare modificare ulterioară din aceeași sesiune. Branch-ul rămâne mereu la 1 commit.
3. **Înainte de push, întreb explicit**: "totul ok sau mai vrei schimbări?" Dacă cere modificări → amend + reia întrebarea. Dacă e ok → push.
4. **Push o singură dată**, apoi `git checkout main` automat. După push, nu mai amend + force-push fără cerere explicită — schimbări noi = branch nou.
5. **PR-ul îl face utilizatorul manual.** Nu rulez `gh pr create`. La final, doar raportez branch-ul push-uit.
6. **Excepție: typo-uri / fix-uri de 1 linie** pot merge direct pe `main` dacă utilizatorul cere explicit. Restul intră în workflow-ul de mai sus.
7. **Mesajele de commit** rămân în format Conventional Commits (`feat(scope): ...`, `fix(scope): ...`), aliniat cu prefix-ul branch-ului.
