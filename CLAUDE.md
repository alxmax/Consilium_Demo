# Contributing to Consilium

Acest repo este sursa skill-ului `consilium`. Pentru a-l **folosi**, invocă `/consilium` într-o sesiune Claude Code. Acest fișier acoperă doar **editarea** skill-ului.

## Contract

`SKILL.md` e contractul public. Citește-l înainte de orice modificare — Constitution (4 principii) și workflow-ul în 6 pași guvernează skill-ul, nu doar utilizatorii lui.

## Convenții Python

- **Stdlib-only.** Niciun script nu introduce dependențe externe. Dacă pare necesar, e probabil semn că feature-ul depășește scope-ul skill-ului.
- **Scripts mici, stand-alone.** Fiecare `scripts/*.py` are docstring CLI, `argparse`, JSON I/O. Reuse între scripts merge prin `importlib.util` (vezi `priors.py`), nu prin packaging.
- **No tests dir.** Smoke-test manual prin CLI; vezi `python scripts/validate_report.py < runs/<latest>.json` ca minim.

## Zone autoritative (atinge cu grijă)

- **`prompts/voices/*.md`** — citite de fiecare voce la rulare. O schimbare aici afectează toate deliberările viitoare → `regression_risk` mare în Conservator. Preferă să injectezi context suplimentar în input-ul vocii, nu în prompt.
  - Vocile core: `generator.md`, `control.md`, `conservator.md` — rulate în orice mod
  - Pass-2: `generator_pass2.md`, `control_pass2.md`, `conservator_pass2.md` — folosite doar de Dialectic
  - `skeptic.md` — focal challenger, rulat în `parallel_skeptic`, `dialectic_skeptic`, `skeptic_on_chosen`
  - `<personality>_lens.md` (Pioneer/Architect/Steward) — prepended peste core voices în `trias` și `trias_split`
  - `frontend_domain_lens.md` — draft experimental (Senate R2), fără dispatch entry încă
- **`prompts/senators/*.md`** — cei 7 senatori folosiți doar în mod `senate` (audit pe skill, nu pe cod user). Schimbarea unui prompt modifică distribuția de verdicts pentru audit-uri viitoare.
- **`SKILL.md` Constitution + workflow** — schimbarea pașilor 1-6 rupe formatul JSON așteptat de `aggregator.py` și `validate_report.py`. Modifică deodată ambele.

## Moduri disponibile

Modurile selectabile de user (SKILL.md le documentează în detaliu):

- **Sequential** (default RUND2) — Conservator → Generator → Control single-context.
- **Dialectic** — two-pass cu cross-review în Pass-2 (`scripts/dialectic_merge.py`).
- **Trias** — 3 personalități × 3 voci, vot democratic peste cele 3 chosen-uri (9 sub-agenți).
- **`trias_split`** — Trias cu Sonnet Generator + Haiku verifiers (~3.3× Parallel). Shallow-amplifier pe probleme cu constraint implicit — vezi `experiments/p3-car-wash.html`.
- **`parallel_skeptic`** — Parallel intern + 1 Skeptic focal pe chosen (4 sub-agenți, 1.33× Parallel). Pentru medium-stakes când conf cade în `[0.5, 0.7]`.
- **`dialectic_skeptic`** — Dialectic + 1 Skeptic focal post-Pass-2 (7 sub-agenți, ~2.3× Parallel).
- **`skeptic_on_chosen`** — flag composabil peste orice mod de bază. Advisory by default; opt-in override via `--skeptic-can-override`.

**Parallel removed (RUND2).** Nu mai e selectabil de user. Rămâne ca auto cross-check intern când `magnitude=critical ∧ reversibility=irreversible`, plus audit silențios la fiecare 20 runs.

Modul **`senate`** are scope distinct: audit pe **modificările skill-ului însuși** (7 senatori), nu pe cod user. On-demand only.

## Fișiere locale (gitignored)

- `FEEDBACK.html` — jurnal de uz real, append-only via `scripts/log_feedback.py` (atomic writes). Vezi `scripts/migrate_feedback_md_to_html.py` pentru istoricul migrării din format `.md`.
- `runs/*.json` — output-urile fiecărei deliberări (păstrate `runs/README.md` și `runs/senate/` ca singurele tracked).

## Self-improvement loop

Când editezi skill-ul însuși: rulează `/consilium` pe propria schimbare. Pentru schimbări la prompts core / arhitectură, modul `senate` (7 senatori) e versiunea mai puternică a self-improvement-ului decât deliberarea single-context. Salvează run-ul în `runs/` și loghează în `FEEDBACK.html` prin `log_feedback.py`.

## Git workflow

Reguli pentru orice schimbare non-trivială făcută de Claude în acest repo:

1. **Branch nou de la `main`** înainte de a edita. Naming: `feat/<slug>` pentru feature-uri / capabilități noi, `fix/<slug>` pentru bugfix-uri. Slug în kebab-case, descriptiv (ex. `feat/parallel-voices`, `fix/aggregator-null-confidence`). Doar aceste două prefix-e.
2. **Un singur commit per branch** — primul `git commit`, apoi `git commit --amend --no-edit` (sau cu mesaj nou dacă scope-ul s-a schimbat) la fiecare modificare ulterioară din aceeași sesiune. Branch-ul rămâne mereu la 1 commit.
3. **Înainte de push, întreb explicit**: "totul ok sau mai vrei schimbări?" Dacă cere modificări → amend + reia întrebarea. Dacă e ok → push.
4. **Push o singură dată**, apoi `git checkout main` automat. După push, nu mai amend + force-push fără cerere explicită — schimbări noi = branch nou.
5. **PR-ul îl face utilizatorul manual.** Nu rulez `gh pr create`. La final, doar raportez branch-ul push-uit.
6. **Excepție: typo-uri / fix-uri de 1 linie** pot merge direct pe `main` dacă utilizatorul cere explicit. Restul intră în workflow-ul de mai sus.
7. **Mesajele de commit** rămân în format Conventional Commits (`feat(scope): ...`, `fix(scope): ...`), aliniat cu prefix-ul branch-ului.
