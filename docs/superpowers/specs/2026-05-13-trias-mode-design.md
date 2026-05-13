# Trias Mode — Design Spec

**Date:** 2026-05-13
**Branch:** `feat/trias-spec` (this spec), then `feat/trias-impl` for runtime
**Architecture diagram:** committed on `feat/trias-mode` (`ed8c141`) — this spec is the engineering counterpart.

---

## Goal

Replace the under-specified Ensemble mode with **Trias** — a fixed team of 3 named personalities (Pioneer / Architect / Steward) that each orchestrate their own parallel deliberation with lens prompts, then vote democratically over the 3 chosen candidates.

**Success criterion:**
`/consilium` în mod Trias pe un diff non-trivial produce `runs/<ts>_trias.json` cu `team: "trias"`, `personalities: [...]`, un `vote_pattern` (3-0 / 2-1 / 2-0 / 1-1-1 / 1-1-0 / 1-0-0 / 0-0-0), și `chosen_approach` derivat prin majoritate (sau `null` la stalemate). `python -X utf8 scripts/validate_report.py < runs/<ts>_trias.json` iese cu cod 0.

---

## Background

`SKILL.md §"Ensemble mode (opțional)"` documentează N personalități sampling random cu aggregation ponderată. Nu există orchestrator end-to-end — doar primitive (`personalities.py` pentru sampling, `aggregator.py --scheme weighted` pentru aggregation). E o rețetă, nu un feature.

Trias înlocuiește asta cu:
- **Personalități fixe** denumite (determinist, debuggable)
- **Lens-per-voice** prin prompt injection (diversitate de perspectivă reală)
- **Vot democratic** (majoritate simplă peste 3, cu failure modes explicite)
- **Orchestrator end-to-end** în workflow-ul skill-ului

`docs/architecture.html` documentează modul vizual (commit `ed8c141`). Acest spec acoperă latura inginerească.

---

## 1. Architecture

3 nivele de execuție:

| Nivel | Entitate | Count |
|---|---|---|
| L0 | Orchestrator (Claude main) | 1 |
| L1 | Personalități (Pioneer/Architect/Steward) | 3 |
| L2 | Voci per personalitate (Gen/Ctrl/Cons + lens) | 9 (3×3) |

**Total: 9 sub-agenți voci + 1 orchestrator.**

**Important — personalitățile NU sunt sub-agenți**, sunt **grupări logice**. Orchestratorul dispatchează direct toți 9 sub-agenții voci (3 voci × 3 personalități), etichetând fiecare dispatch cu personality metadata. Weights-urile sunt aplicate la **aggregation time**, nu la dispatch time. Restricția "no nested Agent calls" (vezi `agents/consilium-subagent.md:33`) e respectată prin design.

**Chinese walls:**
- **L1 (între personalități):** niciuna nu vede deliberarea altei personalități
- **L2 (în fiecare personalitate):** Control + Conservator nu se văd între ele (1+2 parallel pattern)

**Lens injection:**
Înainte de fiecare dispatch, orchestratorul concatenează `prompts/<voice>.md` + `prompts/<personality>_lens.md` în system prompt. Lens-ul distorsionează perceptia vocii prin biasul personalității.

---

## 2. Personalities

| Name | Weights (G, C, K) | Lens character (~50-100 words) |
|---|---|---|
| **pioneer** | 0.49, 0.30, 0.21 | "Favor bold approaches with high creative reward. Tolerate moderate risk for novel solutions. New patterns > existing patterns." |
| **architect** | 0.30, 0.49, 0.21 | "Prioritize architectural soundness, test coverage, type safety. Internal consistency > external speed." |
| **steward** | 0.30, 0.30, 0.40 | "Favor minimal-scope, reversible changes. Prefer existing patterns. Blast radius < novelty." |

**Constrângeri pe weights:**
- Fiecare weight în `[0.20, 0.49]` (păstrat din `personalities.py` — niciun voce silențiată, niciuna nu poate domina singură)
- Suma = 1.0

**Aggregate bias (intentional, progress-leaning):**
- Generator weight mean: **0.363** (+9% vs balanced 0.333)
- Control weight mean: **0.363** (+9%)
- Conservator weight mean: **0.273** (−18%)

Team ranks creative + corect candidate-i mai sus decât cei flag-uiți pentru risc, dar Conservator nu poate fi silențiat (K ≥ 0.21 în toate personalitățile) și Steward poate semnaliza riscuri.

---

## 3. Vote mechanics

Fiecare personalitate rulează full parallel mode cu lens → emite `chose: <id> | null`. Orchestratorul colectează 3 chosen-uri, votează.

| Pattern | Înțeles | Confidence | Outcome | FEEDBACK log |
|---|---|---|---|---|
| 3-0 | Unanim | 0.95 | OK auto | `OK` |
| 2-1 | Majoritate + dissent | 0.70 | OK auto | `OK` |
| 2-0 | Majoritate + 1 abținere | 0.75 | OK auto | `OK` |
| 1-1-1 | Fragmentat | null | PEND | `PEND` |
| 1-1-0 | No majoritate (abținere) | null | PEND | `PEND` |
| 1-0-0 | Minoritate slabă (2 abțineri) | null | PEND | `PEND` |
| 0-0-0 | Veto total | null | PEND + retry_suggested | `PEND` |

**Tie-break în 2-1:** câștigătorul e candidatul cu 2 voturi. Nu există tie-break pe scores — pattern-ul vorbește.

**Steward abstain semantics:** când Steward returnează `chose: null` (toate candidates vetoiate de propriul Conservator), e flagged separat în `abstained[]` — semnal semantic mai puternic decât abținerea Pioneer/Architect, pentru că Steward există să afle riscurile.

---

## 4. Output JSON schema

Shape Trias adaugă câmpuri noi (preserva cele existente pentru backward-compat):

```json
{
  "success_criterion": "<string>",
  "verification": "<command or check>",
  "team": "trias",
  "chosen_approach": "<id | null>",
  "personalities": [
    {
      "name": "pioneer | architect | steward",
      "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21},
      "lens": "prompts/pioneer_lens.md",
      "chose": "<id | null>",
      "rationale": "<short explanation>"
    }
  ],
  "vote_pattern": "3-0 | 2-1 | 2-0 | 1-1-1 | 1-1-0 | 1-0-0 | 0-0-0",
  "dissent": [
    {"personality": "<name>", "chose": "<id>", "why_diff": "<text>"}
  ],
  "abstained": [
    {"personality": "<name>", "reason": "all candidates vetoed by lens-tinted Conservator"}
  ],
  "confidence": "<0.0-1.0 | null>",
  "voice_scores": {"generator": 0.0, "control": 0.0, "conservator": 0.0},
  "alternatives": [...],
  "deliberation_log": [
    {"step": "dispatch_personalities", "count": 3, "parallel": true, "sub_agents_total": 9},
    {"step": "vote_tally", "pattern": "2-1", "winner": "approach_A"},
    {"step": "feedback_log", "outcome": "OK", "auto": true}
  ]
}
```

`voice_scores` raportate la nivel top sunt **mean across personalities** (pentru telemetry agregat în `usage.py`).

---

## 5. Implementation scope

### 5.1 `scripts/personalities.py` — REWRITE

**Current:** random rejection sampling al N weight triples.
**New:** listă hardcoded de 3 personalități, fiecare cu name + weights + lens path.

```python
PERSONALITIES = [
    {"name": "pioneer",   "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21}, "lens": "prompts/pioneer_lens.md"},
    {"name": "architect", "weights": {"generator": 0.30, "control": 0.49, "conservator": 0.21}, "lens": "prompts/architect_lens.md"},
    {"name": "steward",   "weights": {"generator": 0.30, "control": 0.30, "conservator": 0.40}, "lens": "prompts/steward_lens.md"},
]
```

CLI:
- `python personalities.py` → emite cele 3 ca JSON array
- `python personalities.py --name pioneer` → emite o singură personalitate
- Vechiul `python personalities.py N --seed X` returnează exit 2 + mesaj migrate

### 5.2 `prompts/pioneer_lens.md`, `prompts/architect_lens.md`, `prompts/steward_lens.md` — NEW

3 fișiere noi, fiecare ~50-100 cuvinte, descriind biasul personalității. Loaded de orchestrator și concatenate la prompts standard ale vocilor înainte de dispatch.

Format:
```markdown
---
personality: pioneer
voice_bias: prepended
---

You are evaluating this change through a Pioneer's lens. Favor bold approaches
with high creative reward. Tolerate moderate risk for novel solutions. New
patterns > existing patterns. When in doubt, prefer the more ambitious option.
```

### 5.3 `scripts/aggregator.py` — ADD SCHEME

Schemă nouă `team_vote`:

**Input:**
```json
{
  "personalities": [
    {"name": "pioneer",   "chose": "approach_A"},
    {"name": "architect", "chose": "approach_A"},
    {"name": "steward",   "chose": "approach_B"}
  ],
  "candidates": [{"id": "approach_A", ...}, {"id": "approach_B", ...}]
}
```

**Output:**
```json
{
  "scheme": "team_vote",
  "vote_pattern": "2-1",
  "chosen": "approach_A",
  "vote_tally": {"approach_A": 2, "approach_B": 1},
  "dissent": [{"personality": "steward", "chose": "approach_B"}],
  "abstained": []
}
```

Înregistrat în `SCHEMES` dict. Validare: exact 3 personalități în input, fiecare cu `name` și `chose`.

### 5.4 `scripts/confidence.py` — EXTEND

Când input-ul are câmpul `vote_pattern`, derivă confidence din mapping table (§3). Când nu, folosește formula existentă utility/variance.

### 5.5 `scripts/build_report.py` — EXTEND

Adaugă asamblare shape Trias: copiază `team`, `personalities`, `vote_pattern`, `dissent`, `abstained` din bundle în raport.

### 5.6 `scripts/validate_report.py` — EXTEND

Acceptă Trias shape. Cerințe specifice:
- `team == "trias"` → trebuie să aibă `personalities` array cu exact 3 elemente
- Fiecare personalitate are `name`, `weights`, `lens`, `chose`
- `vote_pattern` match regex `^[0-3]-[0-3](-[0-1])?$`
- Dacă `chosen_approach == null`, `confidence == null` (sau `vote_pattern ∈ {1-1-1, 1-1-0, 1-0-0, 0-0-0}`)

Shapes non-Trias continuă să funcționeze neschimbat.

### 5.7 `scripts/log_feedback.py` — MINOR

Loghează `vote_pattern` ca metadata column în `FEEDBACK.html` când prezent.

### 5.8 `SKILL.md` — MAJOR EDITS

- **Șterge** §"Ensemble mode (opțional)" integral
- **Adaugă** §"Trias mode (high-stakes opt-in)" — workflow, când să folosești, format output
- **Update** §"Parallel voices mode" pentru a menționa Trias ca extensie
- **Update** §"Resources" table — descrie rolul nou `personalities.py` + lens files noi

### 5.9 `evals/scenarios.json` — ADD CASES

5 scenarii noi pentru regression:
- `trias_unanimous_3_0` — clear winner, expect 3-0
- `trias_majority_2_1` — close scores, expect 2-1 + dissent
- `trias_abstain_2_0` — o personalitate vetoiată, expect 2-0
- `trias_fragment_1_1_1` — 3 chosen diferite, expect null
- `trias_total_veto_0_0_0` — toate vetoiate, expect null + retry_suggested

---

## 6. Out of scope

- **Custom personality configs** (user-defined teams) — defer
- **Iterative Trias** (revision rounds, ca Dialectic) — orthogonal la vote
- **Trias × Dialectic combination** — prea scump (3× × 2× = 6× Parallel)
- **Auto-fallback** (Trias → Parallel pe failure) — preferăm retry explicit user
- **Cost optimization** prin shared candidate space între personalități — sacrifică independența lens

---

## 7. Acceptance criteria

După implementare:

1. `python -X utf8 scripts/personalities.py` outputs 3 personalități cu `name`, `weights`, `lens` fields
2. `python -X utf8 scripts/aggregator.py --scheme team_vote < tests/trias_input.json` outputs `vote_pattern` și `chosen`
3. Rulând `/consilium` în mod `trias` pe un diff non-trivial → produce `runs/<ts>_trias.json`
4. `python -X utf8 scripts/validate_report.py < runs/<ts>_trias.json` iese cu cod 0
5. `python -X utf8 scripts/run_evals.py` passes inclusiv 5 scenarii Trias noi
6. `FEEDBACK.html` afișează coloana nouă `vote_pattern` pentru Trias runs

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Lens prompts cauzează comportament neașteptat al voicilor (ex. Pioneer's Conservator sub-flag-uiește risc) | Empirical eval înainte de promovare — rulează pe diff-uri istorice, compară cu Parallel |
| 9 sub-agenți ating rate limits / timeouts | Throttling la 3 concurrent în orchestrator; failure fallback la `null` pentru personalitatea afectată |
| 1-1-1 fragmentation comună pe cazuri grele — UX prost | Bloc explicit `retry_suggested` + mesaj de escalare clar |
| Ensemble runs existente în `runs/*.json` confuză `usage.py` | Adaugă legacy shape detection; count Ensemble runs separat sau skip |
| Spec drift între HTML și implementare | După impl, re-verifică HTML; dacă nu match, amend HTML în același PR |

---

## 9. Migration notes

- **Referințe Ensemble eliminate din SKILL.md** — bookmark-urile dau 404, mitigated prin §Trias clar replacement
- **`personalities.py N --seed X` nu mai funcționează** — sampling eliminat; CLI change documentat în commit message
- **Vechile `runs/*_ensemble.json`** — lăsate ca atare; `validate_report.py` nu le rejectează; `usage.py` le flag-uiește ca legacy
- **`--scheme weighted`** (cea deja deprecated cu warning) rămâne — folosită de referințe Ensemble în code paths vechi; eliminăm doar după ce Ensemble e complet scoasă

---

## 10. Resolved decisions

Tip de "open question" rezolvat înainte de implementare (commit `dafdbbc` initial avea §10 ca questions; aici sunt răspunsurile lock-uite).

- **Lens position: prepended.** Lens-ul vine ÎNAINTE de prompt-ul vocii. Motivare: directivele principale ale vocii (definite în `prompts/<voice>.md`) override pe conflict — lens-ul biasează percepția, nu rolul. Implementare: orchestrator construiește `<lens content>\n\n---\n\n<voice prompt content>` și pasează la sub-agent.

- **Model tier per personalitate: respectă tabelul existent din §"Parallel voices mode" — Sonnet default, Opus pe Generator pentru ambiguu, Haiku pe Ctrl/Cons pentru diff-uri mici.** Personalitatea nu schimbă model — toate cele 9 voci ascultă aceleași reguli per-voce ca în Parallel mode. Motivare: separarea de concerne — personalitatea decide lens-ul + weights-ul, modelul rămâne decizia voicii.

- **1-1-1 escalation: ask user, nu re-run automat.** Când vot e fragmentat (1-1-1), orchestratorul emite raportul cu `chosen: null`, `confidence: null`, `escalation_reason: "team_fragmented"`, și întreabă userul explicit: *"Trias fragmentat — Pioneer a ales A, Architect B, Steward C. Vrei să: (a) accepți unul, (b) re-rulezi cu constraint, (c) abort?"* Motivare: păstrează confidence-gating philosophy din rest skill (sub 0.7 = întreabă), evită bucle infinite de auto-retry, lasă decizia ambiguă user-ului.

---

## 11. Files touched (summary)

```
modified:
  SKILL.md
  scripts/personalities.py
  scripts/aggregator.py
  scripts/confidence.py
  scripts/build_report.py
  scripts/validate_report.py
  scripts/log_feedback.py
  evals/scenarios.json

new:
  prompts/pioneer_lens.md
  prompts/architect_lens.md
  prompts/steward_lens.md
```

**11 fișiere total (3 noi, 8 modificate).**
