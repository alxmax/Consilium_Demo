# Contributing to Consilium

Acest repo este sursa skill-ului `consilium`. Pentru a-l **folosi**, invocă `/consilium` într-o sesiune Claude Code. Acest fișier acoperă doar **editarea** skill-ului.

## Contract

`SKILL.md` e contractul public. Citește-l înainte de orice modificare — Constitution (4 principii) și workflow-ul în 6 pași guvernează skill-ul, nu doar utilizatorii lui.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

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
- **`prompts/senators/*.md`** — cei 9 senatori folosiți doar în mod `senate` (audit pe skill, nu pe cod user). Schimbarea unui prompt modifică distribuția de verdicts pentru audit-uri viitoare.
- **`SKILL.md` Constitution + workflow** — schimbarea pașilor 1-6 rupe formatul JSON așteptat de `aggregator.py` și `validate_report.py`. Modifică deodată ambele.

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
