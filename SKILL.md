---
name: max-agent
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, or when uncertain between multiple implementation approaches.
---

# Max Agent — Code Deliberation Skill

Pattern de deliberare multi-perspectivă pentru orice modificare de cod. Trei voci independente colaborează pentru a evalua o schimbare:

- **Generator** (creativ) — propune alternative, divergent thinking
- **Control** (analitic) — verifică corectitudine tehnică
- **Conservator** (prudent) — evaluează risc și reversibilitate

## Constitution

Patru principii care guvernează **fiecare** deliberare. Au prioritate când o voce dă o recomandare ce intră în conflict cu ele.

1. **Think before coding.** Nu presupune. Nu ascunde confuzia. Expune tradeoff-urile explicit. Dacă requestul are 2 interpretări plauzibile, listează-le pe ambele ca `candidates` separate — nu alege tăcut.
2. **Simplicity first.** Minimum de cod care rezolvă problema. Refuză abstracții speculative, feature-uri nesolicitate, error handling pentru cazuri imposibile. `do_nothing` e în lista de candidați tocmai pentru asta.
3. **Surgical changes.** Atinge doar ce cere goal-ul. Fără refactor în zone adiacente "cât suntem aici". Conservator-ul măsoară asta prin factor-ul `scope_drift` — respectă un scor mare.
4. **Goal-driven execution.** Înainte de a genera candidate, restate goal-ul ca **success criterion** într-o singură propoziție testabilă. Output-ul final trebuie să includă un pas de **verification** ("cum știm că a funcționat").

*(Adaptat după CLAUDE.md al lui Andrej Karpathy, via [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).)*

## When to use

Activează acest skill când:
- Faci **review de PR** sau diff
- Planifici un **refactor** care atinge 2+ fișiere
- Trebuie să alegi între **mai multe abordări** de implementare
- Ești pe punctul de a face **commit pe cod shared/core**
- Vrei o **assessment de risc** înainte de a accepta o sugestie

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach".

## Workflow

### 1. Gather context & state the goal
Citește schimbarea propusă (diff, fișiere atinse). Identifică:
- Scope: câte fișiere, câte module, câte linii
- Tipul schimbării: bugfix, feature, refactor, cleanup
- Blast radius: cod intern, cod shared, API public

**Apoi formulează `success_criterion`** — o propoziție testabilă care descrie ce înseamnă "schimbarea a reușit". Dacă requestul e ambiguu, **oprește-te și întreabă** (Principle #1) înainte de a continua. Acest criteriu condiționează toate candidate-urile de mai jos.

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
  "success_criterion": "propoziție testabilă din pasul 1",
  "chosen_approach": "approach_id",
  "reasoning": "scurt rezumat al deciziei",
  "verification": "pasul concret prin care confirmi că success_criterion e îndeplinit (ex: rulează `npm test`, verifică endpoint X răspunde 200, măsoară timp de render)",
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

Câmpurile `success_criterion` și `verification` sunt **obligatorii** — sunt cerute de Principle #4 din Constitution.

## Resources

- `prompts/generator.md` — template pentru voce creativă
- `prompts/control.md` — template pentru voce analitică
- `prompts/conservator.md` — template pentru voce skeptică
- `scripts/personalities.py` — rejection sampling pentru ensemble mode
- `scripts/aggregator.py` — 3 scheme de voting

## Feedback loop

Skill-ul învață din uz real prin două artefacte:

- **`runs/`** — la sfârșitul fiecărei deliberări, scrie întregul output (candidates + verdicts + scores + aggregation) ca JSON în `runs/YYYY-MM-DD_HHMM_<short-label>.json`. Schema în `runs/README.md`. Fișierele sunt gitignored (personale).
- **`FEEDBACK.md`** — jurnal manual, o linie per folosire, format `data | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR` (override), `PEND`. Committed în repo ca să persiste între maşini.

### La începutul fiecărei deliberări
Citește **ultimele ~10 intrări** din `FEEDBACK.md`. Dacă apar tipare clare (ex: 3× `OVR` cu nota "Conservator prea agresiv"), ajustează priorii **în deliberarea curentă** (ex: relaxează pragul veto la 0.8, sau marchează explicit unde Conservator e probabil supra-prudent). Nu modifica fișierele skill-ului; doar prompts-urile rămân autoritative.

### La sfârșitul fiecărei deliberări
1. Scrie JSON-ul complet în `runs/`.
2. Cere utilizatorului o singură linie pentru `FEEDBACK.md` (cu `outcome: PEND` dacă încă nu se ştie rezultatul).

### Auditare periodică
```bash
python scripts/feedback.py            # stats globale
python scripts/feedback.py --recent 10 --runs
```
Output-ul arată: rata de succes, override-uri recente, ce scheme s-au folosit cel mai des. Ține ca semnal pentru când să ajustezi `prompts/*.md` sau `veto_threshold`.

## Ensemble mode (opțional)

Pentru schimbări **high-stakes** (migrări DB, modificări de security, refactor mare):

```bash
python scripts/personalities.py 5
```

Generează N=4–6 personalități cu weights random `w ∈ [0.2, 0.4]`, sum = 1.0. Rulează skill-ul de N ori cu personalități diferite, apoi agregă cross-agent prin `--scheme weighted`.

Folosește când o singură deliberare nu e suficientă și vrei diversitate suplimentară.
