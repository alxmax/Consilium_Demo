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

### Procedură manuală de cross-check Limite (când editezi un prompt senator)

Nu există script CI care validează ortogonalitatea automat — în repo nu rulează CI. Înainte să faci merge la o schimbare în `prompts/senators/*.md`:

1. **Citește cele 7 secțiuni `## Limite` consecutiv.** Pentru fiecare senator, întrebarea de control e: *"Ce NU fac eu? Lista include explicit fiecare alt senator cu domeniul lui?"*
2. **Verifică matricea de mai sus.** Coloana "Output structurat distinct" trebuie să rămână 1:1 cu un senator — niciun câmp dintr-un senator nu trebuie să apară (ca producere) în alt senator.
3. **Test de overlap negativ:** dacă tocmai ai adăugat o frază în secțiunea `## Specialitate` a unui senator, caută aceeași responsabilitate în `## Specialitate` la ceilalți 6. Dacă apare → contradicție de scope; alege un senator unic care primește responsabilitatea.
4. **Test funcțional:** rulează `python -X utf8 scripts/test_senate_synth.py` — suita verifică structural că toate 7 prompturile există și au secțiunile cerute (nu validează semantic, dar prinde structuri rupte).

De ce nu există script: validarea semantică a non-overlap-ului între prompturi NL necesită NLP, nu stdlib. Un keyword-count pe `## Limite` produce false positives pe negații împărtășite (ex: "NU evaluez risc" apare la mai mulți senatori cu sensuri diferite) și false negatives pe overlap real exprimat în vocabular distinct. Verificarea manuală pe matricea § 2 e mai fiabilă decât un script naiv.

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

## 8. Cross-questions (extensie viitoare — NU în MVP)

> **Status:** documentată, neimplementată. MVP-ul curent e single-pass parallel. Această secțiune descrie *vision-ul* — pentru când acumulezi date care arată că merită cost-ul.

Cross-questions transformă Senatul din 7 voci independente într-un grup deliberativ care își poate clarifica pozițiile reciproc. În deliberarea istorică RUND2, **3 senatori și-au schimbat poziții** post-cross-questions (Musk, Wittgenstein, Confucius) — semnal că dinamica funcționează.

### 8.1 Cele 5 Legi ale Senatului

| # | Lege | Esență |
|---|---|---|
| 1 | Răspuns obligatoriu | Fiecare senator răspunde pe fiecare punct — direct, prin întrebare, sau prin reformulare. **Interzis** "nu am opinie" |
| 2 | Cross-questions limitate | Maximum **3 cross-questions per senator per punct**. Previne spam și ramificare infinită. |
| 3 | Blocaj → vot majoritar 5 | Dacă 2 senatori intră în impas, **ceilalți 5 votează**. 7 impar → niciodată 50/50. |
| 4 | Sinteza doar la final | Aggregator pe Senat rulează DUPĂ toate punctele (evită contagiunea de poziții). |
| 5 | Auditabilitate | Toate runde + cross-questions + schimbări de poziție salvate în `runs/senate/`. |

### 8.2 Matricea cross-questions (cine cu cine)

Fiecare senator poate adresa întrebări fiecăruia altul (matrice 7×7, diagonala goală). Perechi observate empiric ca productive în RUND2 marcate cu ★:

```
              W   A   C   S   Mu  D   N
            ┌───┬───┬───┬───┬───┬───┬───┐
Wittgenst.  │ — │ • │ • │ ★ │ • │ • │ • │  ★ = pereche care a schimbat poziții
            ├───┼───┼───┼───┼───┼───┼───┤      în RUND2 (semnal de productivitate)
Aurelius    │ • │ — │ • │ • │ • │ ★ │ ★ │  • = pereche posibilă (toate sunt permise)
            ├───┼───┼───┼───┼───┼───┼───┤
Confucius   │ • │ • │ — │ • │ ★ │ • │ • │
            ├───┼───┼───┼───┼───┼───┼───┤
Socrate     │ ★ │ • │ • │ — │ • │ • │ • │
            ├───┼───┼───┼───┼───┼───┼───┤
Musk        │ • │ • │ ★ │ • │ — │ • │ ★ │
            ├───┼───┼───┼───┼───┼───┼───┤
Dimon       │ • │ ★ │ • │ • │ • │ — │ ★ │
            ├───┼───┼───┼───┼───┼───┼───┤
Napoleon    │ • │ ★ │ • │ • │ ★ │ ★ │ — │
            └───┴───┴───┴───┴───┴───┴───┘
```

**De ce sunt productive:** Wittgenstein↔Socrate (semantic vs asumpții, overlap pe "ce e nedeclarat"), Aurelius↔Dimon/Napoleon (risc abstract vs concret), Musk↔Napoleon (cost calitativ vs cantitativ), Musk↔Confucius (delete vs precedent).

### 8.3 Flow runde (max 3 per senator per punct)

```
   Runda 1: paralel, toți 7 răspund simultan pe input identic
              │
              ▼
   ┌─────────────────────────────────┐
   │ Outputs colectate.              │
   │ Orchestrator detectează:        │
   │  - voturi opuse (potențial      │
   │    blocaj, vezi §8.4)           │
   │  - pattern de cross-question    │
   │    ("întreb pe <senator>...")   │
   └────────────────┬────────────────┘
                    │
   ┌────────────────┴────────────────┐
   │  Există cross-questions?        │
   └──┬──────────────────────────┬───┘
      │ NU                       │ DA
      ▼                          ▼
   senate_synth.py     ┌─────────────────────────┐
   (verdict imediat)   │  RUNDA 2: dispatch focal│
                       │  Senator X (cu max 3    │
                       │  cross-Q used so far)   │
                       │  primește întrebarea Y, │
                       │  răspunde. Counter X+1. │
                       └────────────┬────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │  X mai are <3 cross-Qs? │
                       │  Mai sunt întrebări?    │
                       └──┬──────────────────┬───┘
                          │ NU               │ DA
                          ▼                  ▼
                   sinteză finală        RUNDA 3 (max)
                                         apoi STOP forțat
                                         pentru senatorul X
```

### 8.4 Blocaj resolution (Lege 3)

```
   2 senatori (X și Y) după 3 cross-Qs au poziții opuse:
        X: GO    Y: STOP
              │
              ▼
   ┌──────────────────────────────────┐
   │  Ceilalți 5 senatori primesc:    │
   │  - argumentul lui X (cu evidence)│
   │  - argumentul lui Y (cu evidence)│
   │  - întrebare: care e mai puternic│
   └────────────────┬─────────────────┘
                    │
                    ▼  (5 voturi: X | Y)
        ┌───────────────────────────┐
        │  Majoritate (cel mult 4-1)│
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
     X câștigă                   Y câștigă
   (GO contează)              (STOP contează)

   Verdictul pe punctul ăla = poziția câștigătoare
```

Senatul are **7 impar** → 2 în impas + 5 votanți = niciodată 50/50.

### 8.5 Ce înseamnă pentru orchestrator când implementezi

Schimbări față de MVP-ul curent:
- **Dispatch multi-round** — nu doar 1 ciclu paralel, ci 2-3 cicluri secvențiale (Runda 1 paralel, runde 2-3 doar pentru senatorii care primesc cross-questions)
- **State tracking** — counter `cross_questions_used[senator][point]` per senator per punct
- **Routing cross-questions** — parser pe output pentru "întrebare către <senator>" → dispatch focal pe acel senator
- **Blocaj detection** — orchestrator detectează 2 voturi opuse persistente după 3 runde → dispatch celor 5 senatori neutri
- **Aggregator schema schimbat** — `vote_counts` → `vote_counts_per_round[]` cu schimbări de poziție track-uite

Cost estimat: ~2-3× MVP-ul curent (per senatorii care intră în cross-questions; restul ies devreme).

### 8.6 Indicator de calitate: schimbări de poziție

În RUND2 reală, 3 senatori au schimbat poziții post-cross-questions. Asta e **semnalul** că dinamica funcționează — nu schimbi opinia oarbă, schimbi după ce auzi un counter-argument concret. Un Senat care converge **mereu** fără schimbări de poziție e suspect (groupthink prin structură).

Track-uiește în bundle:
```json
"position_changes": [
  {"senator": "musk", "point": 3, "from": "STOP", "to": "MODIFY", "trigger": "cross-Q from confucius about precedent"}
]
```

## 9. MVP-status

### 9.1 Cele 5 Legi: active vs suspendate în MVP

`prompts/senators/SENAT-todo-rol-legi-functii.md` în `experiments/New phase senat/` declară 5 Legi pentru deliberarea Senatului (vezi §8.1). MVP-ul curent **nu** implementează toate cele 5. Tabelul de mai jos clarifică ce e activ vs suspendat — fără asta, secțiunea Senate mode din SKILL.md pretinde implicit conformitate cu toate cele 5 Legi, ceea ce e fals.

| # | Lege | Status MVP | Cum se manifestă în implementare |
|---|---|---|---|
| 1 | Răspuns obligatoriu | **Activ** (parțial) | Senator absent → marcat în `senators_absent[]`; senator prezent fără `vote` parseable → counted ca MODIFY (vot conservativ). Forma "nu am opinie" interzisă structural prin prompt; absența silentioasă tratată ca MODIFY, nu ca încălcare a Legii 1 — decizie deliberată documentată aici. |
| 2 | Cross-questions max 3 per senator per punct | **Suspendat** | MVP e single-pass parallel. Cross-questions documentate ca §8 future extension; nu există dispatch multi-round. |
| 3 | Blocaj → vot majoritar de 5 | **Suspendat** | Necesită Legea 2 implementată întâi. Documentat ca §8.4. |
| 4 | Sinteza doar la final | **N/A în MVP** | Aplicabilă doar cu multi-round; sinteza curentă e oricum o singură dată (după Pass 1). |
| 5 | Auditabilitate în `runs/senate/` | **Activ** | `senate_synth.py` scrie collision-safe în `runs/senate/<timestamp>-<label>.json`. Folder gitignored (consecvent cu `runs/*.json`) — auditabilitate locală. |

**De ce conturile:** Legile 2–4 sunt aspirational pentru deliberare deliberativă multi-runde. MVP-ul deservește Functia 1 (audit pre-implementare) cu o singură rundă paralelă; e adecvat pentru pre-implementation gating și nu pretinde să replice dinamica RUND2 reală până nu acumulăm 3+ invocări care arată că simple parallel e insuficient.

### 9.2 Disposition self-validation run (2026-05-16_1632)

Run-ul de self-validation a emis verdict **MODIFY** cu 4 modify_requests (Wittgenstein, Socrate, Musk, Dimon). Tabelul de mai jos înregistrează dispoziția fiecărei cereri în implementarea finală — fără asta, MVP-ul ar fi shipped pe un baseline incomplet.

| Senator | Cerere | Status | Unde se vede |
|---|---|---|---|
| Wittgenstein | Operational definitions pentru "end-to-end Senate run", "does not touch existing voices/modes", absent-senator semantics | **Resolved** | `SKILL.md` Senate mode → secțiunea "Operational definitions" |
| Wittgenstein | Fix `collect_risks` asymmetry (Aurelius/Confucius/Musk dropped) | **Resolved** | `collect_risks()` șters complet; doar `collect_modify_requests` + `collect_warnings` rămân (`scripts/senate_synth.py`) |
| Socrate | Comandă concretă de falsificare pentru "end-to-end" — fixture reproducând verdict cunoscut | **Resolved** | `scripts/senate_synth_fixture.json` + 9-test suite în `scripts/test_senate_synth.py` |
| Socrate | Test explicit byte-identical pe voci core (zero-touch verification) | **Resolved** | `SKILL.md` Senate mode → secțiunea "Operational definitions" → predicat `git diff` exact |
| Socrate | Confirmare empirică: dispatch 7-parallel rulat real cu Sonnet 4.6 | **Resolved** | `runs/senate/2026-05-16_1632-self-validation.json` cu 7 voturi reale |
| Socrate | Documentează quorum behavior sub absent (>=3 absent) | **Resolved** | `compute_verdict` emite `UNREACHABLE` când `voters_present < 5`; `collect_warnings` emite `quorum_unreachable` warning |
| Musk | Delete `--no-write`, `--label` CLI flags, `bundle['senators_invoked']` | **Resolved** | Toate șterse din `scripts/senate_synth.py` |
| Musk | Delete SKILL.md "Legi (pentru orchestrator)" subsection + verdict table | **Resolved** | SKILL.md Senate mode condensată; verdict rule rămâne doar inline în workflow Step 4 |
| Musk | Simplify `collect_warnings` la unrecognized-vote + structural fields only | **Resolved** | `collect_warnings` curent emite doar: structural field missing, unrecognized vote, quorum_unreachable. "Absent" restating eliminat. |
| Dimon | Validare per-senator: warning dacă senator prezent cu payload incomplet | **Resolved** | `SENATOR_REQUIRED_FIELDS` dict + warning per senator per field lipsă (`scripts/senate_synth.py`) |
| Dimon | Collision detection în `write_bundle` | **Resolved** | Granularitate la secunde (`%Y-%m-%d_%H%M%S`) + suffix `_v2/_v3` la coliziune (`scripts/senate_synth.py:write_bundle`) |
| Dimon | Warning explicit `quorum_unreachable` când GO/STOP devine matematic imposibil | **Resolved** | Verdict `UNREACHABLE` + warning în `collect_warnings` |

**Rămase deferred (nu deficiențe, ci scope future):**

| Item | Status | Plan |
|---|---|---|
| Cross-questions multi-round (Legea 2) | Deferred | §8 future extension; adăugat după ≥3 invocări reale care arată valoare |
| Blocaj resolution prin vot 5 (Legea 3) | Deferred | §8.4; vine în pachet cu Legea 2 |
| Principle extraction din pattern detection | Deferred | După 30+ senate runs reale cu outcome tracking activ |
| Empirical validation Napoleon | Deferred | După 10+ invocări reale, decide retain vs retire |
| Outcome tracking pentru `runs/senate/` (Functia 3 prerequisite) | Deferred | Adaptat din `scripts/mark_outcome.py` când senate run count ≥10 |
| Scope-overlap detector automat între senatori | **N/A** | Înlocuit cu procedura manuală documentată în §2 (NL semantic check nu e fiabil în stdlib) |
| Contradicție în `modify_requests` (Dimon scenario 5) | Acceptat ca limită | User vede toate cele 7 cereri și filtrează manual; Senatul nu joacă rol de arbitru între cereri |
| `proposal` non-empty hard check | Acceptat ca limită | `senate_synth.py` returnează exit 1 + stderr message; nu mai e silent failure |

---

## 10. Smoke test

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
