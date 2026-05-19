# Contributing to Consilium

Acest repo este sursa skill-ului `consilium`. Pentru a-l **folosi**, invocă `/consilium` într-o sesiune Claude Code. Acest fișier acoperă doar **editarea** skill-ului.

## Contract

`SKILL.md` e contractul public. Citește-l înainte de orice modificare — Constitution (4 principii) și workflow-ul în 8 pași guvernează skill-ul, nu doar utilizatorii lui.

Pentru behavioral guidelines (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, Question Everything), vezi global `~/.claude/CLAUDE.md` — se aplică și aici.

## Commands

Stdlib-only, fără test runner. Smoke tests rulate manual prin CLI:

- `python scripts/test_rund2.py` — RUND2 architecture (skeptic_on_chosen, MODE enum, validate_report extras)
- `python scripts/test_feedback_html.py` — `render_feedback_html` + parser round-trip
- `python scripts/test_senate_synth.py` — Senate pipeline end-to-end pe fixture
- `python scripts/run_evals.py` — regression scenarios din `evals/scenarios.json` (subprocess-based, deterministic; exit non-zero la primul FAIL)
- `python scripts/validate_report.py < runs/<file>.json` — Constitution Principle #4 gate; minimul înainte de orice commit care atinge `prompts/voices/` sau `aggregator.py`

Type-check: `pyright` (config: `pyrightconfig.json`, `typeCheckingMode: basic`, Python 3.11, `scripts/` în `extraPaths`).

## Pipeline

Flow canonic al unei deliberări:

1. Voci citesc `prompts/voices/<name>.md`, emit JSON per Constitution
2. `scripts/aggregator.py` merge voice outputs → canonical report
3. `scripts/confidence.py` calculează scorul; `scripts/priors.py` aplică priors
4. `scripts/validate_report.py` e ultimul gate înainte de write în `runs/<ts>_<slug>.json`

Scripts specifice de mod:
- `dialectic_merge.py` — two-pass merge pentru Dialectic
- `senate_synth.py` — sinteză peste cei 9 senatori (Senate mode pe skill)
- `dispatch_senate_on_code.py` — Senate pe cod user (`--on-code`, EXPERIMENTAL_DRAFT)
- `personalities.py` — Trias lens injection (Pioneer/Architect/Steward)

Sub-agent dispatch (Trias, Skeptic, Senate): vezi `agents/consilium-subagent.md`. Toți sub-agenții folosesc `model: "sonnet"` explicit — nu moșteni Opus.

Vizualizare runde Senate: `docs/architecture.html` (deschide local). Benchmark-uri pe probleme reale: `experiments/` (vezi `experiments/p3-car-wash.html`).

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
  - `prompts/lenses/domain_lens.md` — draft experimental (Senate R2), fără dispatch entry încă
- **`prompts/senators/*.md`** — cei 9 senatori folosiți doar în mod `senate` (audit pe skill, nu pe cod user). Schimbarea unui prompt modifică distribuția de verdicts pentru audit-uri viitoare.
- **`SKILL.md` Constitution + workflow** — schimbarea pașilor 0-7 rupe formatul JSON așteptat de `aggregator.py` și `validate_report.py`. Modifică deodată ambele.

## Moduri disponibile

Modurile selectabile de user (SKILL.md le documentează în detaliu):

- **Sequential** (default RUND2) — Conservator → Generator → Control single-context.
- **Dialectic** — two-pass cu cross-review în Pass-2 (`scripts/dialectic_merge.py`).
- **Trias** — 3 personalități × 3 voci, vot democratic peste cele 3 chosen-uri (9 sub-agenți).
- **`trias_split`** — Trias cu Sonnet Generator + Haiku verifiers (~3.3× Parallel). Shallow-amplifier pe probleme cu constraint implicit — vezi `experiments/p3-car-wash.html`.
- **`skeptic_on_chosen`** — flag composabil peste orice mod de bază (+1 sub-agent peste cost). Advisory by default; opt-in override via `--skeptic-can-override`. Auto-trigger pe `confidence ∈ [0.5, 0.7]`. Înlocuiește modurile fixe `parallel_skeptic` (= `parallel + skeptic_on_chosen`) și `dialectic_skeptic` (= `dialectic + skeptic_on_chosen`) — colapsate pe 2026-05-17, nume vechi rămân în `validate_report.py` MODE enum pentru backward-compat.

**Parallel removed (RUND2).** Nu mai e selectabil direct de user (doar via `parallel + skeptic_on_chosen`). Rămâne ca auto cross-check intern când `magnitude=critical ∧ reversibility=irreversible`, plus audit silențios la fiecare 20 runs.

Modul **`senate`** are două scope-uri: (a) audit pe **modificările skill-ului însuși** (default, well-tested, 9 senatori); (b) audit pe **cod user** via flag `--on-code` (EXPERIMENTAL_DRAFT — vezi gate empiric în SKILL.md). On-demand only.

## Fișiere locale (gitignored)

- `FEEDBACK.html` — jurnal de uz real, append-only via `scripts/log_feedback.py` (atomic writes). Vezi `scripts/deprecated/migrate_feedback_md_to_html.py` pentru istoricul migrării din format `.md` (retired one-shot tool).
- `runs/*.json` — output-urile fiecărei deliberări (păstrate `runs/README.md` și `runs/senate/` ca singurele tracked).
- `docs/superpowers/plans/`, `docs/superpowers/specs/` — artefacte de la `superpowers:writing-plans` / `executing-plans` (un fișier per feature non-trivial, naming `YYYY-MM-DD-<slug>.md`).

## Self-improvement loop

Când editezi skill-ul însuși: rulează `/consilium` pe propria schimbare. Pentru schimbări la prompts core / arhitectură, modul `senate` (9 senatori) e versiunea mai puternică a self-improvement-ului decât deliberarea single-context. Salvează run-ul în `runs/` și loghează în `FEEDBACK.html` prin `log_feedback.py`.

## Git workflow

Reguli pentru orice schimbare non-trivială făcută de Claude în acest repo:

1. **Branch nou de la `main`** înainte de a edita. Naming: `feat/<slug>` pentru feature-uri / capabilități noi, `fix/<slug>` pentru bugfix-uri. Slug în kebab-case, descriptiv (ex. `feat/parallel-voices`, `fix/aggregator-null-confidence`). Doar aceste două prefix-e.
2. **Un singur commit per branch** — primul `git commit`, apoi `git commit --amend --no-edit` (sau cu mesaj nou dacă scope-ul s-a schimbat) la fiecare modificare ulterioară din aceeași sesiune. Branch-ul rămâne mereu la 1 commit.
3. **Push automat după commit** — fără să mai întreb. Dacă utilizatorul cere modificări înainte ca push-ul să se fi făcut → amend + push imediat.
4. **Push o singură dată**, apoi `git checkout main` automat. După push, nu mai amend + force-push fără cerere explicită — schimbări noi = branch nou.
5. **PR-ul îl face utilizatorul manual.** Nu rulez `gh pr create`. La final, doar raportez branch-ul push-uit.
6. **Excepție: typo-uri / fix-uri de 1 linie** pot merge direct pe `main` dacă utilizatorul cere explicit. Restul intră în workflow-ul de mai sus.
7. **Mesajele de commit** rămân în format Conventional Commits (`feat(scope): ...`, `fix(scope): ...`), aliniat cu prefix-ul branch-ului.
