---
name: code-deliberation
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, or when uncertain between multiple implementation approaches.
---

# Code Deliberation Skill

Pattern de deliberare multi-perspectivă pentru orice modificare de cod. Trei voci independente colaborează pentru a evalua o schimbare:

- **Generator** (creativ) — propune alternative, divergent thinking
- **Control** (analitic) — verifică corectitudine tehnică
- **Conservator** (prudent) — evaluează risc și reversibilitate

## When to use

Activează acest skill când:
- Faci **review de PR** sau diff
- Planifici un **refactor** care atinge 2+ fișiere
- Trebuie să alegi între **mai multe abordări** de implementare
- Ești pe punctul de a face **commit pe cod shared/core**
- Vrei o **assessment de risc** înainte de a accepta o sugestie

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach".

## Workflow

### 1. Gather context
Citește schimbarea propusă (diff, fișiere atinse). Identifică:
- Scope: câte fișiere, câte module, câte linii
- Tipul schimbării: bugfix, feature, refactor, cleanup
- Blast radius: cod intern, cod shared, API public

### 2. Generator — produce alternative
Folosește `prompts/generator.md`. Cere **3–5 abordări candidate**, inclusiv "do nothing" ca baseline. Stil divergent — nu auto-cenzura pentru risc în acest pas.

Output per candidate: `{id, summary, sketch, rationale}`.

### 3. Control — verifică corectitudine
Folosește `prompts/control.md`. Pentru fiecare candidate verifică:
- Types corect?
- Tests există / pot fi scrise?
- Logică validă (edge cases, error paths)?
- Style consistent cu codebase-ul?

Output per candidate: `{id, valid: bool, issues: [...]}`.

### 4. Conservator — assess risc
Folosește `prompts/conservator.md`. Pentru fiecare candidate **valid**, scorează:
- Diff size (linii atinse)
- Scope drift (atinge zone nelegate de task)
- Regression risk (probabilitate de a sparge ceva)
- Reversibilitate (cât de ușor revii dacă merge prost)

Output per candidate: `{id, risk_score: 0.0–1.0, factors: {...}}`.

### 5. Aggregate
Rulează:
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — orice candidate cu `risk_score > 0.7` primește veto, indiferent de scorurile celorlalți.

Alte scheme disponibile: `majority`, `weighted`.

### 6. Report
Output JSON final:

```json
{
  "chosen_approach": "approach_id",
  "reasoning": "scurt rezumat al deciziei",
  "alternatives": [
    {"id": "...", "summary": "...", "why_not": "..."}
  ],
  "voice_scores": {
    "generator": 0.8,
    "control": 0.9,
    "conservator": 0.4
  },
  "confidence": 0.85,
  "deliberation_log": [
    {"step": "generator", "candidates": [...]},
    {"step": "control", "verdicts": [...]},
    {"step": "conservator", "scores": [...]},
    {"step": "aggregate", "scheme": "...", "result": "..."}
  ]
}
```

## Resources

- `prompts/generator.md` — template pentru voce creativă
- `prompts/control.md` — template pentru voce analitică
- `prompts/conservator.md` — template pentru voce skeptică
- `scripts/personalities.py` — rejection sampling pentru ensemble mode
- `scripts/aggregator.py` — 3 scheme de voting

## Ensemble mode (opțional)

Pentru schimbări **high-stakes** (migrări DB, modificări de security, refactor mare):

```bash
python scripts/personalities.py 5
```

Generează N=4–6 personalități cu weights random `w ∈ [0.2, 0.4]`, sum = 1.0. Rulează skill-ul de N ori cu personalități diferite, apoi agregă cross-agent prin `--scheme weighted`.

Folosește când o singură deliberare nu e suficientă și vrei diversitate suplimentară.
