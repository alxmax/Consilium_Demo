# Senate — Arhitectură vizuală

> Audit pre-implementare pentru modificări la skill-ul `consilium` însuși. Cu 7 perspective independente, on-demand only.
> **Citește înainte:** secțiunea "Senate mode (`senate`)" din [`SKILL.md`](../../SKILL.md). Acest doc e schemele; SKILL.md e contractul.

---

## 1. Unde stă Senatul în `consilium`

`consilium` are 3 layere distincte. Senatul e layer-ul de **governance** — nu intervine pe întrebări regulate, intervine doar când skill-ul însuși urmează să fie modificat.

```
┌──────────────────────────── consilium ────────────────────────────┐
│                                                                    │
│  ┌─── DELIBERATION LAYER (per-question) ───┐                       │
│  │   Generator  ─→  Control  ─→  Conservator│  ← /consilium        │
│  │   (divergent)   (correct)    (risk)      │    parallel/dialectic│
│  └────────────────────┬─────────────────────┘    trias/skeptic     │
│                       │                                            │
│                       ▼                                            │
│  ┌─── AGGREGATION LAYER ────────────────┐                          │
│  │   aggregator.py → confidence.py →    │                          │
│  │   build_report.py → validate_report  │                          │
│  └────────────────────┬─────────────────┘                          │
│                       │                                            │
│                       ▼                                            │
│              runs/<file>.json (per-deliberare)                     │
│                                                                    │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                    │
│  ┌─── SENATE LAYER (governance, on-demand) ──────────────────┐    │
│  │                                                            │    │
│  │   7 senators parallel  →  senate_synth.py  →  verdict     │    │
│  │   (audit skill change)    (aggregate JSON)    (GO/        │    │
│  │                                                MODIFY/    │    │
│  │                                                STOP)      │    │
│  │                                                            │    │
│  └─────────────────────┬──────────────────────────────────────┘    │
│                        │                                           │
│                        ▼                                           │
│              runs/senate/<file>.json (audit jurnal)                │
└────────────────────────────────────────────────────────────────────┘
```

**Reguli de delimitare:**
- Întrebare user (cod, design, refactor) → **Deliberation + Aggregation** (modurile clasice)
- Modificare la `consilium` însuși (prompturi, scripts, SKILL.md) → **Senate**
- Cele două nu se invocă niciodată împreună pe aceeași execuție.

---

## 2. Cei 7 senatori și lensele lor

Fiecare senator e o **perspectivă cognitivă distinctă** — nu un alter-ego al unei voci core. Scope-ul lor e declarat în secțiunea `## Limite` din fiecare prompt și NU trebuie să se suprapună.

```
                          PROPUNERE
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌─────────────────┐              ┌─────────────────┐
    │  WITTGENSTEIN   │              │    AURELIUS     │
    │  ─────────────  │              │  ─────────────  │
    │  semantic       │              │  reversibility  │
    │  operational    │              │  × magnitude    │
    │  testabil?      │              │  proporțional?  │
    └────────┬────────┘              └────────┬────────┘
             │                                │
    ┌────────┴────────┐              ┌────────┴────────┐
    │   CONFUCIUS     │              │    SOCRATE      │
    │  ─────────────  │              │  ─────────────  │
    │  hierarchy +    │              │  hidden         │
    │  precedent      │              │  assumptions    │
    │  cine decide?   │              │  ce presupui?   │
    │  s-a mai făcut? │              │  load-bearing?  │
    └────────┬────────┘              └────────┬────────┘
             │                                │
    ┌────────┴────────┐              ┌────────┴────────┐
    │     MUSK        │              │    DIMON        │
    │  ─────────────  │              │  ─────────────  │
    │  aggressive     │              │  stress test +  │
    │  deletion       │              │  counterparty   │
    │  delete-able?   │              │  ce dacă pică?  │
    │  add-back 10%   │              │  silent fail?   │
    └────────┬────────┘              └────────┬────────┘
             │                                │
             └───────────────┬────────────────┘
                             │
                             ▼
                  ┌─────────────────┐
                  │    NAPOLEON     │
                  │  ─────────────  │
                  │  cost + terrain │
                  │  câți tokens?   │
                  │  starea oper.?  │
                  └─────────────────┘
```

**Matricea de specializare** (verifică ortogonalitatea):

| Senator | Întrebare cheie | Output structurat distinct |
|---|---|---|
| Wittgenstein | "E definit operațional?" | `vague_terms_found[]` |
| Aurelius | "E proporțional cu stake-ul?" | `reversibility`, `magnitude`, `quadrant` |
| Confucius | "Cine are autoritate? Avem precedent?" | `hierarchy_check`, `precedent_search[]` |
| Socrate | "Ce presupui fără să declari?" | `hidden_assumptions[]` cu `load_bearing` |
| Musk | "Ce poți șterge?" | `components_attacked[]` cu vote keep/delete/simplify |
| Dimon | "Ce dacă eșuează?" | `stress_scenarios[]` cu `failure_mode` |
| Napoleon | "Cât costă? În ce stare ești?" | `cost_estimate`, `terrain_check` |

Toate trebuie să emită câmpul **`vote`** (`GO|MODIFY|STOP`) și **`modify_request`** (string).

---

## 3. Flow de dispatch (de la propunere la verdict)

Senatul nu se invocă automat. Orchestrator-ul (Claude când execută `/consilium senate`) urmează acest flow:

```
USER:   /consilium senate "<propunere>"
                  │
                  ▼
   ┌──────────────────────────────────┐
   │  Orchestrator (Claude session)   │
   │  - Citește prompts/senators/*.md │
   │  - Formulează input identic      │
   └──────────────┬───────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────┐
   │  DISPATCH PARALEL (7×)           │
   │  model: "sonnet" explicit        │
   ├──────────────────────────────────┤
   │  ┌─ Agent: Wittgenstein ─┐       │
   │  ├─ Agent: Aurelius ─────┤       │
   │  ├─ Agent: Confucius ────┤       │
   │  ├─ Agent: Socrate ──────┤  ◄── toți primesc același input
   │  ├─ Agent: Musk ─────────┤       (propunere + context +
   │  ├─ Agent: Dimon ────────┤        prompt-ul lor inline)
   │  └─ Agent: Napoleon ─────┘       │
   └──────────────┬───────────────────┘
                  │
                  ▼ (7 JSON-uri în paralel)
   ┌──────────────────────────────────┐
   │  Orchestrator colectează output  │
   │  - Retry 1× pe JSON malformat    │
   │  - Marchează `absent` pe eșec    │
   │  - Construiește senate_input.json│
   └──────────────┬───────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────┐
   │  scripts/senate_synth.py         │
   │  ───────────────────────────     │
   │  1. tally(7 voturi)              │
   │  2. compute_verdict(quorum=5/7)  │
   │  3. collect_modify_requests      │
   │  4. collect_warnings (structural)│
   │  5. write_bundle (collision-safe)│
   └──────────────┬───────────────────┘
                  │
                  ▼
        runs/senate/<timestamp>-<label>.json
                  │
                  ▼
   ┌──────────────────────────────────┐
   │  Orchestrator prezintă user-ului │
   │  - verdict + ce înseamnă         │
   │  - modify_requests (concrete)    │
   │  - warnings (structural anomalii)│
   └──────────────────────────────────┘
```

---

## 4. Logica verdictului

Regula e simplă, dar are un caz nou (`UNREACHABLE`) pe care implementarea anterioară îl masca:

```
                      ┌──── INPUT: 7 voturi ────┐
                      │  (sau mai puține dacă   │
                      │   senatorii sunt absent)│
                      └────────────┬────────────┘
                                   │
                                   ▼
                   ┌─────────────────────────────────┐
                   │  voters_present = #(prezenți)   │
                   └────────────────┬────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                                       ▼
        voters_present < 5                       voters_present >= 5
                │                                       │
                ▼                                       │
        ┌───────────────┐                               │
        │  UNREACHABLE  │                               │
        │  (quorum      │                               │
        │   imposibil)  │                               │
        │  + warning    │                               │
        └───────────────┘                               │
                                                        ▼
                                          ┌────────────────────────┐
                                          │ count(GO), count(STOP) │
                                          └───────────┬────────────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────────┐
                          ▼                           ▼                           ▼
                  GO >= 5/7              STOP >= 5/7                  altfel
                          │                           │                           │
                          ▼                           ▼                           ▼
                  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
                  │      GO       │         │     STOP      │         │    MODIFY     │
                  │  procedeezi   │         │  revizuie sau │         │  aplică       │
                  │               │         │  override     │         │  modify_      │
                  │               │         │  explicit     │         │  requests     │
                  └───────────────┘         └───────────────┘         └───────────────┘
```

**De ce default-ul e MODIFY:**
Senatul e advisory. Verdict-ul `MODIFY` nu blochează — semnalează că au rămas concerns concrete care merită aplicate sau respinse explicit, nu ignorate tăcut. `GO` și `STOP` sunt convergențe puternice (≥5/7 acord); orice altă combinație e considerată semnal de dezbatere → `MODIFY`.

**De ce UNREACHABLE e separat:**
Dacă 3+ senatori sunt absenți, restul de 4 nu pot atinge matematic quorum-ul de 5 pentru GO sau STOP. Default-ul MODIFY ar fi semantic înșelător — verdict-ul nu e "modificați propunerea", e "verdict structurally biased; orchestrator trebuie să escaladeze". Synth emite warning explicit + verdict `UNREACHABLE`.

---

## 5. Hartă fișiere

```
consilium/
├── SKILL.md                              ← secțiunea "Senate mode (`senate`)"
├── prompts/
│   ├── generator.md                      ← voce core (nu se atinge)
│   ├── control.md                        ← voce core (nu se atinge)
│   ├── conservator.md                    ← voce core (nu se atinge)
│   ├── skeptic.md                        ← voce focală (nu se atinge)
│   └── senators/                         ◄── ADĂUGAT
│       ├── wittgenstein.md
│       ├── aurelius.md
│       ├── confucius.md
│       ├── socrate.md
│       ├── musk.md
│       ├── dimon.md
│       └── napoleon.md
├── scripts/
│   ├── aggregator.py                     ← nu se atinge
│   ├── confidence.py                     ← nu se atinge
│   ├── ...                               ← nu se atinge
│   ├── senate_synth.py                   ◄── ADĂUGAT
│   └── senate_synth_fixture.json         ◄── ADĂUGAT (smoke test)
├── runs/
│   ├── <date>_<label>.json               ← per-deliberare standard
│   └── senate/                           ◄── ADĂUGAT
│       └── <date>_<label>.json           ← per-audit Senate
└── docs/senate/
    └── architecture.md                   ← acest fișier
```

**Principii de izolare:**
1. **Zero modificări la voci core sau scripts deliberative.** Verifică: `git diff <base>..HEAD -- prompts/{generator,control,conservator,skeptic}*.md scripts/{aggregator,confidence,...}.py` → empty.
2. **Storage separat.** `runs/senate/` e gitignored (`runs/senate/*.json`) — istoric local, parallel cu `runs/*.json`.
3. **Cleanup-safe.** Dacă ștergi `prompts/senators/` + `scripts/senate_synth.py` + `runs/senate/` + secțiunea din SKILL.md, consilium standard rămâne funcțional 100%.

---

## 6. Comparație cu modurile existente

| Mod | Sub-agenți | Cost vs Parallel | Scope | Trigger |
|---|---|---|---|---|
| `sequential` | 1 orchestrator | 0.33× | întrebare user | manual / default |
| `parallel` | 3 | 1× | întrebare user | default |
| `parallel_skeptic` | 4 | 1.33× | întrebare user, conf ∈ [0.5, 0.7] | auto conf-gated |
| `dialectic` | 6 | 2× | întrebare user cu trade-offs | manual |
| `dialectic_skeptic` | 7 | 2.3× | întrebare user medium-stakes | manual |
| `trias` | 9 | 3× | întrebare user high-stakes / ireversibilă | manual |
| `trias_split` | 9 (Sonnet+Haiku) | 1× | trade-off ortogonal cost/diversitate | manual |
| **`senate`** | **7** | **~2.3×** | **modificare la skill** | **manual on-demand only** |

`senate` e singurul mod ce auditează **skill-ul însuși**. Toate celelalte operează pe cod / decizii user. Aceleași 7 sub-agenți ca `dialectic_skeptic`, dar perspective complet diferite (audit governance vs. cross-review per-întrebare).

---

## 7. Self-improvement loop

Conform CLAUDE.md original: *"Când editezi skill-ul însuși: rulează `/consilium` pe propria schimbare."* Cu Senatul:

```
   modific consilium  ─→  /consilium senate "<schimbarea mea>"
                                    │
                                    ▼
                          7 senatori audit
                                    │
                                    ▼
                              verdict
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                                       ▼
              GO                                  MODIFY / STOP
                │                                       │
                ▼                                       ▼
        commit + push                       aplic modify_requests
                                                        │
                                                        ▼
                                                    re-run (opțional)
                                                        │
                                                        ▼
                                                 commit + push
```

Bundle-ul rămâne în `runs/senate/<timestamp>-<label>.json` ca jurnal — chiar dacă procedezi împotriva verdictului (override explicit), audit-ul e păstrat.

---

## 8. Limitări cunoscute (MVP)

Senatul curent e MVP single-pass parallel. Extensii documentate în [`experiments/New phase senat/todos/SENAT-todo-rol-legi-functii.md`](../../experiments/New%20phase%20senat/todos/SENAT-todo-rol-legi-functii.md):

| Limitare | Status | Plan viitor |
|---|---|---|
| Cross-questions între senatori | Lipsă | Adăugat când ≥3 invocări reale arată că ar fi prins ceva important |
| Blocaj resolution prin vot majoritar | Lipsă | Necesar doar cu cross-questions; vine în pachet |
| Principle extraction din pattern detection | Lipsă | După 30+ runs Senat reale (outcome tracking activ) |
| Scope-overlap detector între senatori | Lipsă | Validare statică în CI dacă vreodată CI-uri pe repo |
| Empirical validation Napoleon pe 5-10 întrebări | Lipsă | După 10+ invocări, decide retain vs retire |

---

## 9. Smoke test

Fixture pentru verificarea că pipeline-ul rulează end-to-end fără sub-agenți reali:

```bash
cat scripts/senate_synth_fixture.json | python -X utf8 scripts/senate_synth.py
```

**Așteptare:**
- `verdict: MODIFY`
- `vote_counts: {GO: 3, MODIFY: 3, STOP: 1}`
- `warnings: ["senator 'dimon' voted but omitted/empty 'stress_scenarios' — that axis of audit is silent"]`
- Fișier nou în `runs/senate/<timestamp>-fixture-smoke.json`

Dacă orice diferă → bug în synth sau în fixture; investighează.

---

**Citește mai departe:**
- [`SKILL.md`](../../SKILL.md) — contractul (Senate mode section)
- [`scripts/senate_synth.py`](../../scripts/senate_synth.py) — docstring + implementarea synthesizer-ului
- [`experiments/New phase senat/`](../../experiments/New%20phase%20senat/) — istoricul deliberativ care a dus la această arhitectură
