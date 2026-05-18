# 2026-05-19 — architecture.html rework design

## Goal

Rescriere `docs/architecture.html` astfel încât **un inginer fără context Consilium să poată parcurge pagina narativ și să înțeleagă arhitectura** fără să recurgă la SKILL.md sau cod sursă.

Constrângeri:
- Audiență: inginer fără experiență pe Consilium specific; **fără analogii**, fără simplificare cu metafore.
- Densitate vizuală mare — fiecare concept cheie cu diagramă dedicată; țintă ~25-35 diagrame total (acum ~12).
- Jargonul proiect-specific (RUND2, lens, focal challenger, scope gate, veto cascade) **rămâne**, dar este însoțit prima dată de definiție concisă; glosar local la finalul fiecărui tab.
- **Păstrăm structura 6 tab-uri** (Overview / Modes / Voices / Internals / Reference / Efficiency).
- Single layer rewrite — nu există mod "simple/tehnic" toggleabil.

## Approach: Story-driven, fără template fix

Fiecare tab își găsește forma proprie (no rigid 5-act anatomy). Story-arc per tab, ordine narativă firească, diagrame interleaved cu prosul. Constanta între tab-uri: fiecare tab se închide cu **glosar local** (6-8 termeni) cu link la fișier sursă.

## Per-tab design

### Tab 1 — Overview

Story: *Ce e Consilium → de ce 3 voci → cum decid împreună → ce iese*.

Ordine:
1. Ce e — paragraf + diagrama hook existentă (diff → 3 voices → aggregate → winner)
2. De ce 3 voci, nu una — secțiune nouă, 2-3 propoziții + **D1** (1 vs. 3 lenses cu blind spots)
3. Cele 3 voci pe scurt — card-uri condensate (rol într-o linie); detalii rămân în Voices
4. Pipeline 0→6 — Mermaid existent păstrat + step cards condensate (rol + output canonic; tăiat scriptul repetat)
5. Aggregation:
   - **D2** veto cascade vizual (acum doar tabel)
   - Tabelul 8-component veto cascade (păstrat)
   - 3 scheme + exemplul numeric (păstrate)
6. Confidence gate & retry — Mermaid existent (păstrat)
7. Feedback loop — SVG existent (păstrat)
8. Three-layer architecture (RUND2) — la final, "zoom out" pentru Deliberation/Aggregation/Senate
9. Glosar local

Diagrame noi: **D1** (1 vs. 3 voices), **D2** (veto cascade vizual), **D3** (mini-card SVG per voce, 3 buc), **D4** (scope_gate skip vs. deliberate flow).

### Tab 2 — Modes

Story: *Iată modurile → cum aleg → deep-dive Trias integrat*.

Ordine:
1. **Decision tree "ce mod folosesc?"** — secțiune nouă în top, **D5** (SVG mare cu branching).
2. **Cost map** — **D6** scatter SVG (axă cost vs. independență).
3. Modurile în ordine de complexitate crescândă:
   - Sequential (default)
   - Dialectic
   - Trias (cu deep-dive integrat sub card)
   - Trias split-model
   - skeptic_on_chosen (flag)
   - Senate (card scurt, pointer la Reference)
   - Parallel (auto) + Sequential naive — collapsed la final
4. Trias deep-dive integrat sub cardul Trias (SVG existent 3 personalități + chinese walls păstrat, tabel failure modes păstrat, "use when/avoid when" păstrate). **Nu mai e secțiune separată la final.**
5. Cost multipliers comparison table — păstrat, condensat
6. Glosar local: *chinese wall, strip_context, skeptic on chosen, lens, magnitude/reversibility, scope_gate*

Tăiat: tabela "Routing — ce mod pentru ce situație" (înlocuită de D5).

Diagrame noi: **D5** (decision tree), **D6** (cost vs. independence map), **D7** (mode comparison side-by-side: cine vede ce, când), **D8** (sub-agent dispatch anatomy).

### Tab 3 — Voices

Story: *3 voci canonice → ce fac/nu fac → 3 lenses → Skeptic → Domain lens experimental*.

Ordine:
1. **Roles overview** — **D9** SVG cu cele 3 voci, săgeți de ordine + ce primește fiecare
2. Card-uri detaliate Generator / Control / Conservator — păstrate (rol · principii · ce poate · ce nu are voie · contract)
3. **Input/output per voce** — secțiune nouă, **D10** (3 mini-diagrame, concret JSON-like)
4. **Sequential vs. Trias dispatch** — **D11** SVG comparație: strip vs. lens-prepended sub-agents
5. 3 personality lenses (Pioneer/Architect/Steward) — card-uri existente + **D12** heatmap 3×3 weights
6. Skeptic — focal challenger — secțiune existentă + **D13** "ce vede / ce nu vede"
7. Domain lens (experimental) — păstrat scurt, badge EXPERIMENTAL
8. Glosar local: *clarity gate, tokens_budget, irreversibility_flag, glossary_fail, net_concern, addressable, meta_scope_mismatch, prepended lens*

Diagrame noi: **D9-D13** (5).

### Tab 4 — Internals

Story (memory + flow patterns ca un singur narrativ):

1. **De ce Consilium are memorie** — paragraf hook + SVG 3 tiers stacked (existent)
2. Cele 3 tiers Short/Medium/Long — card-uri existente + **D14** "ce scrie/citește fiecare tier" (matrice scripts × tiers cu R/W markers)
3. Signals priors.py — tabel existent + **D15** state machine (clean → blocked → resolved)
4. Observe → Think → Act → Learn — Mermaid existent (păstrat — center didactic)
5. [confirmed] marker — secțiune existentă + **D16** timeline (T₀ OK subiectiv → T₁ regression → mark_outcome → T₂ priors pondereaza 2×)
6. CLI memory.py — păstrat
7. Flow patterns interactive — diagrama node-based existentă + Play tour (păstrate). Adăugăm 3 propoziții de intro ce explică Play tour.
8. Glosar local: *priors, stale_pending, weighted_bad_rate, episodic memory, soft signal, fail-open, [confirmed] marker, pend_pressure*

Diagrame noi: **D14-D16** (3). Logica JS pentru Play tour păstrată ca-i.

### Tab 5 — Reference

Story: *Unde stă ce → scripts → git → dialectic detail → Senate canonic*.

Ordine:
1. **Repo map** — secțiune nouă în top, **D17** SVG arbore directoare cu 1-liner per nod (prompts/, scripts/, runs/, experiments/, docs/, SKILL.md, CLAUDE.md, FEEDBACK.html)
2. Scripts inventory grupat pe rol — păstrat din Overview rail, reorganizat în 3 clustere: *deliberation pipeline · feedback loop · maintenance*. **D18** tabel-diagramă vizuală.
3. Git workflow — păstrat + **D19** lifecycle (branch → edit → commit → amend loop → push → checkout main → user PR)
4. Dialectic merge detail — secțiune existentă păstrată + mini snippet `revision_log` JSON
5. **Senate (extins) — devine secțiunea canonică**:
   - Cei 7 senatori cu nume + 1-liner optică (Wittgenstein/Aurelius/Confucius/Socrate/Musk/Dimon/Napoleon) — **D20** card grid
   - **D21** Senate flow (7 sub-agents → 7 verdicts → tally → advisory)
   - Scope: skill changes vs. `--on-code` experimental + gate empiric
6. Glosar local: *senator, advisory verdict, dispatch, prepended prompt, on-demand audit, revision_log, --on-code flag, empirical gate*

Tăiat: redundanța dintre "fișiere autoritative" și inventory de scripts. Fără secțiune TODO/known-limitations.

Diagrame noi: **D17-D21** (5).

### Tab 6 — Efficiency

Story: *Cât plătești per OK?*

Ordine:
1. **Întrebarea centrală** — paragraf + **D22** bar chart tokens/OK per mod
2. **Cost anatomy** — **D23** SVG breakdown (input + output + per-sub-agent overhead — explică de ce Trias ≈ 3× Sequential)
3. Tokens per mod — tabele existente grupate: standard · split/composabil · audit
4. Cost/OK ratio — **D24** extensie tabel existent cu coloană "tokens per OK confirmat" (placeholder dacă datele lipsesc)
5. Când merită cost-ul — 3-4 propoziții + **D25** 2×2 quadrant (cost-of-mistake × cost-of-running)
6. Benchmark methodology — paragraf scurt cu pointer la `experiments/`; notă: același `--effort` pe toate modurile, modelele decid intern
7. Glosar local: *tokens/OK, baseline, multiplier vs Parallel, effort flag, OK/PEND/BAD/OVR*

Diagrame noi: **D22-D25** (4).

## Diagram inventory total

| Tab | Diagrame noi | Existente păstrate | Subtotal |
|---|---|---|---|
| Overview | 4 (D1-D4) | hook SVG, pipeline Mermaid, confidence Mermaid, feedback SVG | ~8 |
| Modes | 4 (D5-D8) | Trias flow SVG mare, cost-grid, failure-table | ~7 |
| Voices | 5 (D9-D13) | — | 5 |
| Internals | 3 (D14-D16) | 3 tiers stacked SVG, agent loop Mermaid, flow patterns interactive | ~6 |
| Reference | 5 (D17-D21) | dialectic merge diagram (dacă există) | ~5-6 |
| Efficiency | 4 (D22-D25) | tabele cost | ~4 |
| **Total** | **25 noi** | **~9-12 păstrate** | **~34** |

Aliniat cu ținta "dens, 25-35 diagrame".

## Tehnologie

- Mermaid 10 (existent) pentru flow-uri standard
- SVG inline custom pentru diagrame ne-flow (heatmap, matrix, quadrant, breakdown, timeline)
- CSS existent reluat; eventual variabile noi pentru act-coloration dacă necesar
- JS existent păstrat (tab switching, play tour, banner dismiss)
- Zero dependențe externe noi (stdlib-only consistent cu convențiile repo-ului — în acest caz: zero npm/CDN nou)

## Out of scope

- Mod toggle "simple/tehnic"
- Pagină nouă separată (gen `how-it-works.html`)
- Schimbări la SKILL.md / scripts Python
- TODO/known-limitations section în Reference
- Bilingv (rămâne română)
- Mockups intermediare prin Visual Companion

## Success criteria

1. Un inginer fără context Consilium poate parcurge fiecare tab fără să întrebe "ce înseamnă X" (toți termenii proiect-specific au definiție la prima apariție SAU în glosarul tabului).
2. Fiecare tab are între 4 și 8 diagrame, plus glosar local.
3. Total ~30-35 diagrame, mix Mermaid + SVG custom.
4. Pagina rămâne single-file HTML + CSS + JS separat (nu introducem build step).
5. Toate diagramele Mermaid render-uiesc fără erori pe Chrome/Firefox curent.
6. Conținutul tehnic existent **nu se pierde** — doar se rearanjează, condensează, sau primește vizualizare nouă.

## Open content questions (resolve during implementation)

Discrepanțe între `CLAUDE.md` actual și `architecture.html` curent care trebuie aliniate în rewrite:

- **Număr de pași pipeline**: arhitectura curentă spune "Pașii 0 → 6"; `CLAUDE.md` zice "pașii 0-7 rupe formatul JSON". Verifică `SKILL.md` ca sursă canonică înainte de rewrite și folosește acea numerotare uniformă.
- **Număr de senatori**: arhitectura curentă listează "7 senatori (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon)"; `CLAUDE.md` menționează "modul senate (9 senatori)". Verifică `prompts/senators/` ca sursă canonică pentru număr exact + nume; adjust D20 + Senate flow accordingly.
- **`scripts/deprecated/`**: există referință la `scripts/deprecated/migrate_feedback_md_to_html.py` în `CLAUDE.md`. Dacă există în repo, repo map (D17) trebuie să includă nodul `scripts/deprecated/`.

## Risks

- **Regresie pe ancore interne** (`#trias-deepdive` etc.): Trias deep-dive migrează sub cardul Trias din Modes. Verifică link-uri intra-page după rewrite.
- **CSS bloat**: 25 SVG-uri inline pot crește dimensiunea fișierului. Verifică total < 250KB minified (acum ~85KB HTML + 30KB CSS).
- **Glossary maintenance**: termeni definiți în 6 glosare locale pot diverge față de SKILL.md. Convenție: prima sursă autoritară rămâne SKILL.md; glosarele HTML linkează la fișiere sursă.
- **Mermaid + SVG mix**: stil vizual eterogen. Soluție: paleta CSS unică aplicată ambelor; convenția existentă (`themeVariables` pentru Mermaid + variabile CSS pentru SVG) e suficientă.
