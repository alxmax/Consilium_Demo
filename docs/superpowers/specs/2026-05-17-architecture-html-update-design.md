# Architecture HTML Update — Design Spec

**Date:** 2026-05-17
**Scope:** 3 fișiere HTML — docs/architecture.html (main), docs/senate/architecture.html (redesign), consilium-viz.html (șters)

---

## Obiectiv

Unificarea documentației vizuale Consilium:
- `docs/architecture.html` devine fișierul principal cu tot conținutul mergeuit
- Toate fișierele primesc diagrame Mermaid
- `docs/senate/architecture.html` e redesignat să fie consistent vizual cu fișierul principal
- `consilium-viz.html` e șters (conținut mutat în main)

---

## 1. docs/architecture.html — modificări

### Tab-uri existente (neatinse ca structură)
| Tab | Status | Modificare |
|-----|--------|------------|
| Arhitectură | existent | Adaugă `<script src="mermaid">` în `<head>` |
| Flow | existent | Adaugă Mermaid `flowchart TD` overview compact **deasupra** step-cards HTML existente |
| Moduri | existent | Nicio schimbare |
| Trias | existent | Nicio schimbare |
| Patterns | existent | Nicio schimbare (SVG interactiv, nu se reproduce în Mermaid) |

### Tab-uri noi (din consilium-viz.html)
| Tab | Conținut | Tip diagramă |
|-----|----------|--------------|
| Dialectic Flow | Pass 1 izolat + Pass 2 cross-review + reguli per-voce | Mermaid `sequenceDiagram` + `flowchart LR` |
| TODO Matrix | 26 TODO-uri impact×efort cu tooltip hover | SVG bubble chart (JS) — Mermaid nu suportă scatter |
| Memory & Loop | Observe→Think→Act→Learn + memory tiers | Mermaid `flowchart LR` + cards HTML |

### Tehnic
- Adaugă `<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>` în `<head>`
- `mermaid.initialize({ startOnLoad: true, securityLevel: 'loose' })` în `<script>` existent
- CSS pentru `.mermaid { text-align: center; }` deja prezent în consilium-viz — copiat în main
- Tab-urile noi urmează același pattern CSS existent (`section.tab`, nav buttons)
- JS TODO Matrix mutat 1:1 din consilium-viz (funcțiile `drawMatrix`, `jitter`, array `todos`)

---

## 2. docs/senate/architecture.html — redesign complet

### Design system
Identic cu `docs/architecture.html`:
- CSS variables: `--bg #0f1419`, `--gold #fbbf24`, `--ctl #60a5fa`, `--con #f87171`, `--accent #34d399`
- Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`
- Header sticky cu tab-uri (`nav.tabs`)
- Background mesh gradient identic

### Tab-uri (§1-§10 reorganizate)
| Tab | Secțiuni acoperite | Diagrame Mermaid |
|-----|-------------------|-----------------|
| Overview | §1 — Layere | `flowchart TD` cu 3 layere (Deliberation / Aggregation / Senate) |
| Senatori | §2 — Cei 7 senatori | Cards HTML redesignate (conținut păstrat, CSS actualizat) |
| Dispatch | §3 — Flow de dispatch | `sequenceDiagram`: Orchestrator → 7 senators → senate_synth.py → verdict |
| Verdict | §4 — Logica verdictului | `flowchart TD`: voters_present → GO/MODIFY/STOP/UNREACHABLE |
| Fișiere & Mod | §5-§6 — Hartă fișiere + Comparație moduri | File tree HTML + tabel redesignat |
| Self-improvement | §7-§8 — Self-improvement loop + Cross-questions | HTML redesignat (no additional Mermaid) |
| Limitări & Test | §9-§10 — Limitări cunoscute + Smoke test | HTML redesignat |

### Elemente păstrate din versiunea veche
- Conținutul senator cards (name, spec, question, field) — redesign CSS only
- Tabelele comparative §6
- Lista limitărilor §9
- Procedura smoke test §10

---

## 3. consilium-viz.html — eliminat

Fișier șters din repo după ce conținutul e confirmat prezent în `docs/architecture.html`.

Verificare înainte de ștergere:
- [ ] Tab "Dialectic Flow" prezent și funcțional în main
- [ ] Tab "TODO Matrix" prezent și funcțional în main  
- [ ] Tab "Memory & Loop" prezent și funcțional în main

---

## Criterii de succes

1. `docs/architecture.html` se deschide în browser, toate 8 tab-urile funcționează, diagramele Mermaid se randează
2. `docs/senate/architecture.html` arată consistent cu fișierul principal (același design system), toate 7 tab-urile funcționează, diagramele Mermaid se randează
3. `consilium-viz.html` nu mai există în repo
4. TODO Matrix (bubble chart) funcționează cu hover tooltip în noul tab din main
5. Patterns tab din main rămâne funcțional (interactivitate SVG neafectată)

---

## Ordine de implementare

1. Adaugă Mermaid + 3 tab-uri noi în `docs/architecture.html`
2. Verifică funcționarea în browser
3. Redesignează `docs/senate/architecture.html` complet
4. Verifică funcționarea în browser
5. Șterge `consilium-viz.html`
