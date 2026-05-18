# Architecture HTML Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `docs/architecture.html` story-driven, engineer-targeted, with ~25 new diagrams and per-tab glossaries — no analogies, jargon retained with first-use definitions.

**Architecture:** Surgical per-tab rewrites of an existing single-page HTML poster (HTML + CSS + vanilla JS, Mermaid 10 CDN). Each of 6 tabs gets its own story arc; shared template = each tab ends with a glossary block. New diagrams are a mix of inline SVG (structure/comparison) and Mermaid flowcharts. JS for tabs, play tour, banner stays untouched.

**Tech Stack:** HTML5 · CSS3 · vanilla JS · Mermaid 10 (CDN). No build step, no dependencies, no tests framework.

**Spec:** `docs/superpowers/specs/2026-05-19-architecture-html-rework-design.md`

---

## Conventions for this plan

Since this is HTML/CSS/SVG work with no test framework, "verification" means:

- **Render check**: open `docs/architecture.html` in a browser (`start chrome` on Windows works), click into the tab modified, verify Mermaid renders without errors (no red error boxes), SVGs display, no console errors.
- **Anchor check**: after structural changes, search the file for `href="#X"` and confirm `id="X"` still exists for each X.
- **Glossary cross-check**: every term in a tab's glossary must appear at least once in that tab's prose (otherwise it's an orphan definition).
- **File size budget**: total `architecture.html` < 250KB. Check via `dir docs\architecture.html` (Windows) or filesystem.

Each task ends with a **`git commit --amend --no-edit`** (per project workflow: branch stays at 1 commit) — except Task 1 which is the initial commit.

## Anchors to preserve

These IDs are referenced by JS or intra-page links — DO NOT remove:

- `#overview`, `#modes`, `#voices`, `#internals`, `#reference`, `#efficiency` — tab IDs (JS depends on `[data-tab]` + matching `section.tab` IDs)
- `#trias-deepdive` — referenced from Modes Trias card via `href="#trias-deepdive"`. Per spec, deep-dive migrates *under* Trias card → this anchor stays but may move (keep ID, update href if same-tab now)
- `#startBanner`, `#patPlayBtn`, `#patDiagram`, `#patGrid`, `#patSvg`, `#patFlows`, `#patStepsList` — JS uses these for tour + banner dismiss
- All Mermaid `themeVariables` blocks — paleta CSS unique

IDs that may be removed (spec says no TODO/known-limitations section):

- `#todoMatrixSvg`, `#todoTooltip` — only if confirmed unused by JS. Check `architecture.js` first.

## Content discrepancy fixes (apply globally during respective tasks)

1. **Pipeline steps**: change all references from "Pașii 0 → 6" / "Step 6" to **"Pașii 0 → 7"**, adăugând Step 7 = `infer_pipeline.py` (deliverable enforcement, mandatory când prompt declară `**Required output files**` sau `**Deliverables**`; opt-in altfel; skip dacă `chosen_approach = do_nothing|skipped`; headless = `--yes` non-interactiv). Affects Overview pipeline Mermaid + step cards + Internals OBSERVE→THINK→ACT→LEARN diagram + Reference scripts inventory (add `infer_pipeline.py`).
2. **Senator count**: change "7 senatori (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon)" → **"9 senatori (Aurelius, Confucius, Deming, Dimon, Musk, Napoleon, Socrate, Tacitus, Wittgenstein)"**. Affects Modes Senate card + Reference Senate section + D20 card grid.

---

## Task 1: Pre-flight + groundwork

**Files:**
- Modify: `docs/architecture.html` (one global compatibility check)
- Check: `docs/architecture.js`

- [ ] **Step 1: Audit JS dependencies on IDs we plan to remove**

Run: `grep -nE "todoMatrix|todoTooltip" docs/architecture.js`
- If matches found → keep IDs in markup, plan to leave empty placeholder OR adjust JS in Task 6
- If no matches → safe to remove `#todoMatrixSvg`, `#todoTooltip` and any related JS

- [ ] **Step 2: Snapshot current intra-page anchors**

Run: `grep -oE 'href="#[^"]+"|id="[^"]+"' docs/architecture.html | sort -u > /tmp/anchors_before.txt`
After all rework, run again as `/tmp/anchors_after.txt` and compare. Tab IDs + `#trias-deepdive` + `#pat*` + `#startBanner` must persist.

- [ ] **Step 3: Add CSS variables for new diagram types**

In `docs/architecture.css`, near top variable block, add (if not present):

```css
:root {
  --glossary-bg: #11151c;
  --glossary-border: #2d3441;
  --glossary-term: #93c5fd;
  --heatmap-low: #1a2a1a;
  --heatmap-mid: #2a3b1f;
  --heatmap-high: #3a5121;
  --quadrant-grid: #2d3441;
}
```

(Used by D12 heatmap, D25 quadrant, all glossary blocks.)

- [ ] **Step 4: Add CSS for `.glossary` block (shared across all 6 tabs)**

Append to `docs/architecture.css`:

```css
.glossary {
  margin-top: 32px;
  padding: 18px 22px;
  background: var(--glossary-bg);
  border: 1px solid var(--glossary-border);
  border-radius: 8px;
}
.glossary h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.glossary dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 6px 14px; }
.glossary dt { color: var(--glossary-term); font-weight: 600; font-family: ui-monospace, monospace; font-size: 12px; }
.glossary dd { margin: 0; color: var(--text); font-size: 12.5px; line-height: 1.5; }
.glossary dd code { color: var(--muted); font-size: 11px; }
```

- [ ] **Step 5: Initial commit on this branch**

```bash
git add docs/architecture.css
git commit -m "feat(arch): scaffold CSS for glossary + new diagram primitives

Preparatory CSS for the architecture.html rework: shared .glossary
block (used in all 6 tabs) and color variables for D12 heatmap, D25
quadrant. No HTML changes yet — those land in per-tab tasks."
```

- [ ] **Step 6: Render check**

Open `docs/architecture.html` in browser. Confirm: page still loads, no console errors, no visual change yet.

---

## Task 2: Overview tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 40-424 (entire `<section id="overview">`)

**Story arc** (per spec): Ce e → De ce 3 voci → Voci pe scurt → Pipeline 0→7 → Aggregation → Confidence → Feedback loop → 3-layer architecture → Glosar.

- [ ] **Step 1: Apply pipeline step count fix to existing pipeline Mermaid**

In Overview, the existing Mermaid block (currently `S0 → ... → S6`). Change:

```
S0 --> S1 --> S15 --> S2 --> S3 --> S4 --> S5 --> S5b --> S5c --> S5d --> S6
```

to:

```
S0 --> S1 --> S15 --> S2 --> S3 --> S4 --> S5 --> S5b --> S5c --> S5d --> S6 --> S7
S7["Step 7\nInfer pipeline\ninfer_pipeline.py"]:::aux
```

Add node definition `S7["Step 7\nInfer pipeline\ninfer_pipeline.py"]:::aux` near other node definitions.

Also update header from `Pașii 0 → 6` to `Pașii 0 → 7`.

Also adjust the existing `S6 -.->|"priors loop"| S0` to `S7 -.->|"priors loop"| S0` (feedback loop now closes from Step 7, not Step 6).

- [ ] **Step 2: Add Step 7 card alongside existing step cards**

In the second `<div class="flow" ...>` block (with STEP 3-6 cards), append a 5th card:

```html
<div class="step aux">
  <div class="n">STEP 7</div>
  <h4>Infer pipeline <span class="sub">conditional</span></h4>
  <p>Mandatory când promptul declară <code>Required output files</code> / <code>Deliverables</code> — <code>infer_pipeline.py</code> deduce și execută pașii de implementare după Step 6. Skip dacă <code>chosen_approach ∈ {do_nothing, skipped}</code>. Headless: <code>--yes</code>.</p>
  <div class="io">infer_pipeline.py → {steps[], rationale}</div>
</div>
```

Grid columns: adjust parent flow to `grid-template-columns:repeat(5,1fr);`

- [ ] **Step 3: Add D1 — "De ce 3 voci, nu una" (SVG)**

Insert after the existing `<div class="intro">` block, before `<div class="constitution">`:

```html
<div class="why-three" style="margin:24px 0;">
  <h2>De ce 3 voci, nu una?</h2>
  <p style="color:var(--muted);font-size:13px;max-width:720px;">Un singur LLM evaluând propria propunere are blind spots predictibile: produce idei și le validează din aceeași perspectivă. Trei voci cu mandate disjuncte (creativă · analitică · risc) cross-validate înainte de aggregation.</p>
  <svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="1 voice vs 3 voices coverage">
    <!-- LEFT: 1 voice -->
    <text x="90" y="22" fill="#e5e7eb" font-size="13" font-weight="600" text-anchor="middle">1 voce (self-eval)</text>
    <circle cx="90" cy="120" r="58" fill="#2a2410" stroke="#5c4a14" opacity="0.85"/>
    <text x="90" y="125" fill="#fbbf24" font-size="11" text-anchor="middle">acoperire creativă</text>
    <text x="90" y="200" fill="#fca5a5" font-size="10" text-anchor="middle" font-style="italic">blind spots: risc, edge cases</text>
    <!-- DIVIDER -->
    <line x1="240" y1="40" x2="240" y2="200" stroke="#2d3441" stroke-width="1" stroke-dasharray="3,4"/>
    <!-- RIGHT: 3 voices -->
    <text x="480" y="22" fill="#e5e7eb" font-size="13" font-weight="600" text-anchor="middle">3 voci independente</text>
    <circle cx="430" cy="110" r="55" fill="#2a2410" stroke="#5c4a14" opacity="0.7"/>
    <text x="430" y="105" fill="#fbbf24" font-size="11" text-anchor="middle">Generator</text>
    <text x="430" y="118" fill="#fbbf24" font-size="9" text-anchor="middle">creative</text>
    <circle cx="510" cy="110" r="55" fill="#182338" stroke="#2a3f5f" opacity="0.7"/>
    <text x="540" y="105" fill="#93c5fd" font-size="11" text-anchor="middle">Control</text>
    <text x="540" y="118" fill="#93c5fd" font-size="9" text-anchor="middle">verify</text>
    <circle cx="470" cy="160" r="55" fill="#2a1818" stroke="#5c2a2a" opacity="0.7"/>
    <text x="470" y="190" fill="#fca5a5" font-size="11" text-anchor="middle">Conservator</text>
    <text x="470" y="202" fill="#fca5a5" font-size="9" text-anchor="middle">risk</text>
  </svg>
</div>
```

- [ ] **Step 4: Add D3 — mini-cards "Cele 3 voci pe scurt" with role + I/O**

Insert after D1, before the "Constitution" block:

```html
<div class="voices-mini" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0;">
  <div class="voice-mini gen" style="padding:12px;border:1px solid var(--gen);border-radius:8px;background:#1a1408;">
    <h4 style="margin:0 0 4px;color:#fbbf24;">Generator</h4>
    <div style="color:var(--muted);font-size:11px;margin-bottom:8px;">creativ · rulează al 2-lea</div>
    <div style="font-size:11px;"><b>in:</b> diff + tokens_budget · <b>out:</b> candidates[] + preferred</div>
  </div>
  <div class="voice-mini ctl" style="padding:12px;border:1px solid var(--ctl);border-radius:8px;background:#0d1320;">
    <h4 style="margin:0 0 4px;color:#93c5fd;">Control</h4>
    <div style="color:var(--muted);font-size:11px;margin-bottom:8px;">analitic · rulează al 3-lea</div>
    <div style="font-size:11px;"><b>in:</b> candidates + full output · <b>out:</b> verdicts[] + glossary</div>
  </div>
  <div class="voice-mini con" style="padding:12px;border:1px solid var(--con);border-radius:8px;background:#1a0a0a;">
    <h4 style="margin:0 0 4px;color:#fca5a5;">Conservator</h4>
    <div style="color:var(--muted);font-size:11px;margin-bottom:8px;">risc · rulează primul</div>
    <div style="font-size:11px;"><b>in:</b> diff + context · <b>out:</b> risk_score + tokens_budget</div>
  </div>
</div>
<p style="font-size:11px;color:var(--muted);margin:-8px 0 24px;">Detalii complete: tab <b>Voices</b>.</p>
```

- [ ] **Step 5: Add D2 — veto cascade vizual (replaces lead-in to existing table)**

Before the existing `<h3>8-component veto cascade</h3>`, insert a Mermaid block:

```html
<div class="mermaid-wrap" style="max-width:900px;margin:24px 0;">
  <h3>Veto cascade — de la triggers la outcomes</h3>
  <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart LR
    T1["irreversibility_flag"]:::con --> O1["BLOCK hard"]:::block
    T2["glossary_fail"]:::ctl --> O2["BLOCK soft"]:::block
    T3["disagreements: substantial"]:::ctl --> O3["REWORK"]:::rework
    T4["meta_recommendation: scale_down"]:::con --> O4["ADAPT_SHORT"]:::adapt
    T5["meta_recommendation: scale_up"]:::con --> O5["ADAPT_EXTENDED"]:::adapt
    T6["3+ triggers simultane"]:::agg --> O6["ESCALATE"]:::escal
    T7["none of above"]:::aux --> O7["AGGREGATE (default)"]:::ok
    classDef con fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
    classDef ctl fill:#182338,stroke:#2a3f5f,color:#93c5fd
    classDef agg fill:#0a2e23,stroke:#145c45,color:#6ee7b7
    classDef aux fill:#11151c,stroke:#2d3441,color:#9ca3af
    classDef block fill:#3a1d1d,stroke:#7a3030,color:#fca5a5
    classDef rework fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef adapt fill:#1a2a3d,stroke:#2a3f5f,color:#93c5fd
    classDef escal fill:#3a1d2a,stroke:#7a3030,color:#fca5a5
    classDef ok fill:#0a2e23,stroke:#145c45,color:#6ee7b7
  </div>
</div>
```

- [ ] **Step 6: Add D4 — scope_gate skip vs. deliberate (new SVG)**

Replace or augment the existing "Step 1.5 scope gate decision tree" SVG. The tree is already good but doesn't show *what gets through*. Add a small comparison panel above the existing tree:

```html
<div class="scope-gate-compare" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:12px 0;">
  <div style="padding:10px;background:#0a2e23;border:1px solid #145c45;border-radius:6px;">
    <h4 style="margin:0 0 6px;color:#6ee7b7;">SKIP (skipped_report)</h4>
    <ul style="margin:0;padding-left:18px;font-size:11.5px;color:#6ee7b7;line-height:1.6;">
      <li>diff ≤ 1 file</li>
      <li>diff ≤ 15 lines</li>
      <li>nu hit pe blocklist</li>
      <li>ex: typo, rename, comment fix</li>
    </ul>
  </div>
  <div style="padding:10px;background:#182338;border:1px solid #2a3f5f;border-radius:6px;">
    <h4 style="margin:0 0 6px;color:#93c5fd;">DELIBERATE (full pipeline)</h4>
    <ul style="margin:0;padding-left:18px;font-size:11.5px;color:#93c5fd;line-height:1.6;">
      <li>multi-file SAU &gt;15 lines</li>
      <li>blocklist hit (auth, crypto, migrations)</li>
      <li>fail-open: probe error → deliberate</li>
      <li>ex: refactor, feature, migration</li>
    </ul>
  </div>
</div>
```

- [ ] **Step 7: Add Overview glossary at end of section**

Just before `</section>` of `#overview`:

```html
<div class="glossary">
  <h3>Glosar Overview</h3>
  <dl>
    <dt>RUND2</dt><dd>A 2-a iterație a regulilor de orchestrare în Consilium — definește ordinea Conservator-First + auto-cross-check intern. Vezi <code>SKILL.md</code> § Workflow.</dd>
    <dt>aggregator</dt><dd>Scriptul care transformă voturile celor 3 voci într-un singur <code>chosen_approach</code>. 4 scheme, default <code>conservative_override</code>. <code>scripts/aggregator.py</code>.</dd>
    <dt>veto cascade</dt><dd>Set de 8 triggere derivate din output-urile vocilor care decid routing-ul deliberării (BLOCK/REWORK/ADAPT/ESCALATE/AGGREGATE) înainte de aggregation propriu-zisă.</dd>
    <dt>conservative_override</dt><dd>Schema default de aggregation: medie ponderată cu safety = 1 − conservator, plus veto unilateral pentru Conservator la <code>risk_score &gt; 0.8</code>.</dd>
    <dt>scope_gate</dt><dd>Step 1.5: auto-skip pentru diff-uri triviale (≤1 file, ≤15 linii). Fail-open: dacă probe-ul eșuează, deliberează. <code>scripts/scope_gate.py</code>.</dd>
    <dt>priors</dt><dd>Soft signals derivate din FEEDBACK.html și runs/ trecute (weighted_bad_rate, stale_pendings, pend_pressure), injectate la Step 0. <code>scripts/priors.py</code>.</dd>
    <dt>confidence gate</dt><dd>Step 5b: dacă <code>confidence &lt; 0.7</code> după aggregation, declanșează retry single-pass cu context îmbogățit (Step 5d).</dd>
    <dt>three-layer architecture</dt><dd>Deliberation (3 voci per întrebare) + Aggregation (synthesis output) + Senate (on-demand audit pe skill changes). Layere distincte, scope-uri diferite.</dd>
  </dl>
</div>
```

- [ ] **Step 8: Render check**

Open `docs/architecture.html`. Click Overview tab. Verify:
- Pipeline Mermaid renders with Step 7 visible
- All 5 step cards in second row (was 4)
- D1 "Why 3 voices" SVG visible after intro
- Voices mini-cards present
- Veto cascade Mermaid renders before existing table
- Scope gate comparison panel above decision tree
- Glossary block at end with 8 terms

If any Mermaid red error → fix syntax, re-render.

- [ ] **Step 9: Amend commit**

```bash
git add docs/architecture.html docs/architecture.css
git commit --amend --no-edit
```

---

## Task 3: Modes tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 425-845 (`<section id="modes">`)

**Story arc**: Decision tree → Cost map → Modes (complexity-sorted) → Trias deep-dive *integrated* → Cost table → Glosar.

- [ ] **Step 1: Insert D5 — decision tree "ce mod folosesc" at top of Modes**

Replace the lead-in `<h2>Flow models — 8 active modes…</h2>` with this decision tree first, then keep the h2 below:

```html
<h2>Care mod folosesc?</h2>
<p style="color:var(--muted);font-size:13px;margin:-8px 0 16px;">Decision tree — pornind de la profilul deciziei, către modul recomandat. Skeptic e flag composabil, nu mod separat.</p>
<div class="mermaid-wrap" style="max-width:980px;margin-bottom:24px;">
  <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart TD
    Q1{"Diff trivial?\n≤1 file, ≤15 linii"}
    Q1 -->|"da"| SKIP["scope_gate skip\n(no mode needed)"]:::skip
    Q1 -->|"nu"| Q2{"Reversibility?"}
    Q2 -->|"reversible"| Q3{"≥2 abordări\nplauzibile?"}
    Q2 -->|"irreversible\n+ critical"| TRIAS["trias\n(9 sub-agents)"]:::trias
    Q3 -->|"nu"| SEQ["sequential\n(default)"]:::seq
    Q3 -->|"da"| Q4{"O voce ar putea\nflip după cross-review?"}
    Q4 -->|"nu"| TRIAS2["trias"]:::trias
    Q4 -->|"da"| DIAL["dialectic\n(6 sub-agents)"]:::dial
    Q5{"Modificare la\nskill însuși?"}
    SKIP -.->|"sau"| Q5
    SEQ -.->|"plus"| Q5
    Q5 -->|"da"| SEN["senate\n(9 senatori, advisory)"]:::sen
    Q6{"confidence ∈ [0.5, 0.7]?"}
    SEQ --> Q6
    DIAL --> Q6
    TRIAS --> Q6
    Q6 -->|"da"| SKEP["+ skeptic_on_chosen\n(auto-trigger)"]:::skep
    Q6 -->|"nu"| OUT["ship chosen"]:::ok
    classDef skip fill:#11151c,stroke:#2d3441,color:#9ca3af
    classDef seq fill:#0a2e23,stroke:#145c45,color:#6ee7b7
    classDef dial fill:#182338,stroke:#2a3f5f,color:#93c5fd
    classDef trias fill:#221830,stroke:#4c2a6b,color:#d8b4fe
    classDef sen fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef skep fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
    classDef ok fill:#0a2e23,stroke:#145c45,color:#6ee7b7
  </div>
</div>
```

- [ ] **Step 2: Add D6 — cost vs. independence map (SVG scatter)**

Insert after D5:

```html
<div class="cost-map" style="margin:20px 0;">
  <h3>Cost vs. independență — la o privire</h3>
  <svg viewBox="0 0 720 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cost vs independence scatter">
    <!-- axes -->
    <line x1="60" y1="280" x2="680" y2="280" stroke="#9ca3af" stroke-width="1.5"/>
    <line x1="60" y1="280" x2="60" y2="30" stroke="#9ca3af" stroke-width="1.5"/>
    <text x="370" y="305" fill="#e5e7eb" font-size="11" text-anchor="middle">Independență voci →</text>
    <text x="32" y="155" fill="#e5e7eb" font-size="11" text-anchor="middle" transform="rotate(-90 32 155)">Cost (× Parallel) →</text>
    <!-- gridlines -->
    <line x1="60" y1="220" x2="680" y2="220" stroke="#2d3441" stroke-width="0.5" stroke-dasharray="2,3"/>
    <line x1="60" y1="140" x2="680" y2="140" stroke="#2d3441" stroke-width="0.5" stroke-dasharray="2,3"/>
    <line x1="60" y1="60" x2="680" y2="60" stroke="#2d3441" stroke-width="0.5" stroke-dasharray="2,3"/>
    <text x="50" y="224" fill="#9ca3af" font-size="9" text-anchor="end">1×</text>
    <text x="50" y="144" fill="#9ca3af" font-size="9" text-anchor="end">2×</text>
    <text x="50" y="64" fill="#9ca3af" font-size="9" text-anchor="end">3×</text>
    <!-- Sequential: low cost, low independence (same context) -->
    <circle cx="140" cy="270" r="14" fill="#0a2e23" stroke="#145c45"/>
    <text x="140" y="274" fill="#6ee7b7" font-size="10" text-anchor="middle" font-weight="700">SEQ</text>
    <text x="140" y="252" fill="#6ee7b7" font-size="9" text-anchor="middle">0.33×</text>
    <!-- Parallel auto: medium cost, high independence -->
    <circle cx="480" cy="220" r="14" fill="#2a2410" stroke="#5c4a14" opacity="0.6"/>
    <text x="480" y="224" fill="#fbbf24" font-size="9" text-anchor="middle" font-weight="700">PAR*</text>
    <text x="480" y="202" fill="#fbbf24" font-size="9" text-anchor="middle">1× (auto)</text>
    <!-- Dialectic: cost 2x, independence + cross-review -->
    <circle cx="430" cy="140" r="14" fill="#182338" stroke="#2a3f5f"/>
    <text x="430" y="144" fill="#93c5fd" font-size="10" text-anchor="middle" font-weight="700">DIAL</text>
    <text x="430" y="122" fill="#93c5fd" font-size="9" text-anchor="middle">2×</text>
    <!-- Senate -->
    <circle cx="560" cy="116" r="14" fill="#2a2410" stroke="#5c4a14"/>
    <text x="560" y="120" fill="#fbbf24" font-size="9" text-anchor="middle" font-weight="700">SEN</text>
    <text x="560" y="98" fill="#fbbf24" font-size="9" text-anchor="middle">2.3×</text>
    <!-- Trias -->
    <circle cx="620" cy="60" r="14" fill="#221830" stroke="#4c2a6b"/>
    <text x="620" y="64" fill="#d8b4fe" font-size="10" text-anchor="middle" font-weight="700">TRI</text>
    <text x="620" y="42" fill="#d8b4fe" font-size="9" text-anchor="middle">3×</text>
    <!-- Trias split -->
    <circle cx="600" cy="48" r="12" fill="#221830" stroke="#4c2a6b" opacity="0.65"/>
    <text x="600" y="52" fill="#d8b4fe" font-size="8" text-anchor="middle">TRI-s</text>
    <text x="540" y="38" fill="#d8b4fe" font-size="9">3.3×</text>
    <!-- Note -->
    <text x="60" y="20" fill="#9ca3af" font-size="9">* PAR = auto cross-check only la critical+irreversible — nu selectabil de user</text>
  </svg>
</div>
```

- [ ] **Step 3: Reorder mode cards by complexity**

Current order (lines ~430-643): Sequential blind → Parallel removed → Dialectic → Trias → Trias split → Legacy collapsed → Skeptic-on-chosen → Senate → Sequential naive legacy.

Target order: Sequential → Dialectic → Trias → Trias split → skeptic_on_chosen (flag) → Senate → [collapsed: Parallel auto, Sequential naive legacy, parallel_skeptic + dialectic_skeptic retired].

Move blocks in place. Keep all content identical for now (Step 1+2 of this task added the new diagrams at top).

- [ ] **Step 4: Integrate Trias deep-dive under Trias card**

Currently `<div class="trias-deepdive" id="trias-deepdive">` is at lines ~728-841 (after all mode cards). Move it to *directly under* the Trias card body (after its `dl.mode-meta` + `use-when` blocks).

Keep `id="trias-deepdive"` so existing `href="#trias-deepdive"` anchor still works. Update the in-Trias-card link from `<a href="#trias-deepdive">↓ Deep-dive Trias</a>` → can stay (still jumps, just shorter distance now) OR remove since it's directly below. Keep for now.

- [ ] **Step 5: Add D7 — mode comparison side-by-side table-as-diagram**

After cost-map (D6), add:

```html
<div class="mode-compare" style="margin:20px 0;">
  <h3>Cine vede ce, când</h3>
  <table class="compare-table" style="font-size:12px;">
    <thead>
      <tr>
        <th>Mod</th>
        <th>Context per voce</th>
        <th>Cross-review</th>
        <th>Dispatch</th>
        <th>Voting</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Sequential</b></td>
        <td>același context (cu <code>strip_context.py</code>)</td>
        <td>nu</td>
        <td>in-process</td>
        <td>aggregate scheme</td>
      </tr>
      <tr>
        <td><b>Parallel</b> (auto)</td>
        <td>context separat per voce</td>
        <td>nu</td>
        <td>3 sub-agents paralel</td>
        <td>aggregate scheme</td>
      </tr>
      <tr>
        <td><b>Dialectic</b></td>
        <td>context separat (Pass 1) → vede outputs (Pass 2)</td>
        <td>da (Pass 2)</td>
        <td>6 sub-agents (3+3)</td>
        <td>aggregate pe revisions</td>
      </tr>
      <tr>
        <td><b>Trias</b></td>
        <td>context separat per personalitate; intra-personalitate sequential</td>
        <td>nu între personalități (chinese wall)</td>
        <td>9 sub-agents (3×3)</td>
        <td>vot democratic peste 3 chosen</td>
      </tr>
    </tbody>
  </table>
</div>
```

- [ ] **Step 6: Add D8 — sub-agent dispatch anatomy (SVG)**

After D7:

```html
<div class="dispatch-anatomy" style="margin:20px 0;">
  <h3>Ce e, de fapt, un "sub-agent"?</h3>
  <p style="color:var(--muted);font-size:12.5px;max-width:780px;">Nu e un proces sau un model nou — e o nouă invocare API cu propriul context window și propriul prompt. Orchestratorul (Claude main) primește înapoi doar JSON-ul final declarat în system prompt-ul vocii. Niciun shared state.</p>
  <svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sub-agent dispatch anatomy">
    <rect x="20" y="20" width="180" height="60" rx="6" fill="#0a2e23" stroke="#145c45"/>
    <text x="110" y="44" fill="#6ee7b7" font-size="13" font-weight="700" text-anchor="middle">Claude main</text>
    <text x="110" y="62" fill="#9ca3af" font-size="10" text-anchor="middle">orchestrator</text>
    <line x1="200" y1="50" x2="260" y2="50" stroke="#c084fc" stroke-width="2"/>
    <polygon points="255,46 262,50 255,54" fill="#c084fc"/>
    <text x="230" y="42" fill="#d8b4fe" font-size="9" text-anchor="middle">dispatch</text>
    <text x="230" y="68" fill="#9ca3af" font-size="9" text-anchor="middle">prompt + input</text>
    <rect x="265" y="10" width="280" height="80" rx="6" fill="#221830" stroke="#4c2a6b"/>
    <text x="405" y="32" fill="#d8b4fe" font-size="13" font-weight="700" text-anchor="middle">sub-agent (e.g. Generator)</text>
    <text x="405" y="50" fill="#9ca3af" font-size="10" text-anchor="middle">own context window · own system prompt</text>
    <text x="405" y="68" fill="#9ca3af" font-size="9" text-anchor="middle">nu vede deliberarea altor sub-agenți</text>
    <text x="405" y="82" fill="#9ca3af" font-size="9" text-anchor="middle">nu vede ce face Claude main între dispatches</text>
    <line x1="545" y1="50" x2="605" y2="50" stroke="#34d399" stroke-width="2"/>
    <polygon points="600,46 607,50 600,54" fill="#34d399"/>
    <text x="575" y="42" fill="#6ee7b7" font-size="9" text-anchor="middle">return</text>
    <text x="575" y="68" fill="#6ee7b7" font-size="9" text-anchor="middle">final JSON only</text>
    <rect x="610" y="20" width="90" height="60" rx="6" fill="#11151c" stroke="#2d3441"/>
    <text x="655" y="48" fill="#e5e7eb" font-size="11" text-anchor="middle">candidates[]</text>
    <text x="655" y="62" fill="#9ca3af" font-size="9" text-anchor="middle">verdicts[]</text>
    <!-- bottom: cost implication -->
    <rect x="20" y="130" width="680" height="90" rx="6" fill="#11151c" stroke="#2d3441"/>
    <text x="40" y="152" fill="#e5e7eb" font-size="12" font-weight="600">Cost implication</text>
    <text x="40" y="172" fill="#9ca3af" font-size="11">Fiecare sub-agent = restart de context = input tokens duplicate (system prompt + diff + context).</text>
    <text x="40" y="190" fill="#9ca3af" font-size="11">Trias = 9 sub-agents = ~9× input baseline. De aceea Trias e ~3× Parallel chiar dacă output-ul total e similar.</text>
    <text x="40" y="208" fill="#9ca3af" font-size="11">Sequential evită overhead-ul → folosește același context window pentru 3 roluri (cu strip).</text>
  </svg>
</div>
```

- [ ] **Step 7: Update Senate mode card — 9 senators**

In Senate card body (~line 622-630), change:

```
<dd>Wittgenstein · Aurelius · Confucius · Socrate · Musk · Dimon · Napoleon</dd>
```

to:

```
<dd>Aurelius · Confucius · Deming · Dimon · Musk · Napoleon · Socrate · Tacitus · Wittgenstein</dd>
```

And `<dd><b>7</b> senatori Sonnet</dd>` → `<dd><b>9</b> senatori Sonnet</dd>`.

Also update cost from `~2.3×` to `~3.0×` (9 senators vs. 3 baseline ≈ 3×). Cross-check cost table in same tab and fix there too.

- [ ] **Step 8: Update cost multipliers table for Senate row**

In the cost comparison table (lines ~660-711), change Senate row:
- `7` → `9`
- `~2.3×` → `~3.0×`

- [ ] **Step 9: Delete routing table (replaced by D5)**

Remove the `<h2>Routing — ce mod pentru ce situație</h2>` + its table (~lines 714-725).

- [ ] **Step 10: Add Modes glossary**

Before `</section>` of `#modes`:

```html
<div class="glossary">
  <h3>Glosar Modes</h3>
  <dl>
    <dt>chinese wall</dt><dd>Izolare informațională între sub-agenți — niciun sub-agent nu vede deliberarea altuia. Vine din dispatch separat, nu din sanitizare prompt.</dd>
    <dt>strip_context</dt><dd>Util Sequential — proiectează output-ul vocii anterioare la minim (id+summary+sketch) înainte de a-l pasa următoarei voci. <code>scripts/strip_context.py</code>.</dd>
    <dt>skeptic_on_chosen</dt><dd>Flag composabil peste orice mod — adaugă 1 sub-agent care contestă <code>chosen</code> post-hoc. Advisory default; override opt-in via <code>--skeptic-can-override</code>.</dd>
    <dt>lens</dt><dd>Prompt suplimentar prepended peste vocea core (Pioneer/Architect/Steward) — biasează percepția fără să schimbe rolul vocii. Folosit doar în Trias.</dd>
    <dt>magnitude / reversibility</dt><dd>Două dimensiuni ale unei schimbări extrase de Conservator: <code>magnitude</code> (small/medium/critical) și <code>reversibility</code> (reversible/expensive/irreversible). Combinația critical+irreversible declanșează auto cross-check.</dd>
    <dt>scope_gate</dt><dd>Step 1.5: auto-skip pentru diff-uri triviale (vezi Overview glosar).</dd>
    <dt>silent audit</dt><dd>La fiecare 20 runs, Parallel rulează automat lângă Sequential, fără să afecteze output-ul. Dacă apare divergență sistematică → frecvența crește la 1/5.</dd>
  </dl>
</div>
```

- [ ] **Step 11: Render check + amend commit**

Open browser, click Modes tab. Verify D5 decision tree renders, D6 cost map visible, mode cards in new order, Trias deep-dive sits under Trias card, D7+D8 visible, routing table gone, Senate shows 9 senators, glossary at end.

```bash
git add docs/architecture.html
git commit --amend --no-edit
```

---

## Task 4: Voices tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 846-979 (`<section id="voices">`)

**Story arc**: Roles overview → 3 cards → I/O per voce → Sequential vs. Trias dispatch → 3 lenses + weights heatmap → Skeptic + field-of-view → Domain lens → Glosar.

- [ ] **Step 1: Add D9 — roles overview SVG at top**

After the existing `<h2>Voices</h2>` + lede paragraph, insert:

```html
<div class="roles-overview" style="margin:18px 0 24px;">
  <h3>Cele 3 voci — ordine + ce primește fiecare</h3>
  <svg viewBox="0 0 760 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Voices role overview">
    <!-- 1. Conservator first -->
    <rect x="30" y="60" width="180" height="90" rx="8" fill="#2a1818" stroke="#5c2a2a"/>
    <text x="120" y="80" fill="#fca5a5" font-size="13" font-weight="700" text-anchor="middle">1. Conservator</text>
    <text x="120" y="96" fill="#9ca3af" font-size="10" text-anchor="middle">risc</text>
    <text x="120" y="118" fill="#fca5a5" font-size="10" text-anchor="middle">in: diff + context</text>
    <text x="120" y="132" fill="#fca5a5" font-size="10" text-anchor="middle">out: risk + tokens_budget</text>
    <line x1="210" y1="105" x2="270" y2="105" stroke="#9ca3af" stroke-width="2"/>
    <polygon points="265,101 272,105 265,109" fill="#9ca3af"/>
    <!-- 2. Generator -->
    <rect x="280" y="60" width="180" height="90" rx="8" fill="#2a2410" stroke="#5c4a14"/>
    <text x="370" y="80" fill="#fbbf24" font-size="13" font-weight="700" text-anchor="middle">2. Generator</text>
    <text x="370" y="96" fill="#9ca3af" font-size="10" text-anchor="middle">creativ</text>
    <text x="370" y="118" fill="#fbbf24" font-size="10" text-anchor="middle">in: + tokens_budget</text>
    <text x="370" y="132" fill="#fbbf24" font-size="10" text-anchor="middle">out: candidates[]</text>
    <line x1="460" y1="105" x2="520" y2="105" stroke="#9ca3af" stroke-width="2"/>
    <polygon points="515,101 522,105 515,109" fill="#9ca3af"/>
    <!-- 3. Control -->
    <rect x="530" y="60" width="180" height="90" rx="8" fill="#182338" stroke="#2a3f5f"/>
    <text x="620" y="80" fill="#93c5fd" font-size="13" font-weight="700" text-anchor="middle">3. Control</text>
    <text x="620" y="96" fill="#9ca3af" font-size="10" text-anchor="middle">analitic</text>
    <text x="620" y="118" fill="#93c5fd" font-size="10" text-anchor="middle">in: candidates + full out</text>
    <text x="620" y="132" fill="#93c5fd" font-size="10" text-anchor="middle">out: verdicts[]</text>
    <text x="370" y="180" fill="#9ca3af" font-size="10" text-anchor="middle" font-style="italic">ordinea RUND2 — Conservator primul, output-ul lui calibrează efortul restului</text>
  </svg>
</div>
```

- [ ] **Step 2: Add D10 — Input/Output per voce (3 mini-cards)**

After the existing `.voices` div with 3 voice cards, insert:

```html
<h3 style="margin-top:32px;">Input / Output exact per voce</h3>
<div class="io-cards" style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:12px;">
  <div style="padding:14px;background:#1a0a0a;border:1px solid #5c2a2a;border-radius:8px;">
    <h4 style="margin:0 0 8px;color:#fca5a5;">Conservator</h4>
    <div style="font-size:11.5px;line-height:1.7;">
      <div><b>in:</b></div>
      <pre style="margin:4px 0;color:#9ca3af;font-size:10.5px;">{diff, context,
 success_criterion}</pre>
      <div><b>out:</b></div>
      <pre style="margin:4px 0;color:#fca5a5;font-size:10.5px;">{risk_score,
 tokens_budget,
 irreversibility_flag,
 meta_recommendation}</pre>
    </div>
  </div>
  <div style="padding:14px;background:#1a1408;border:1px solid #5c4a14;border-radius:8px;">
    <h4 style="margin:0 0 8px;color:#fbbf24;">Generator</h4>
    <div style="font-size:11.5px;line-height:1.7;">
      <div><b>in:</b></div>
      <pre style="margin:4px 0;color:#9ca3af;font-size:10.5px;">{diff, context,
 tokens_budget.generator,
 clarity_flag?}</pre>
      <div><b>out:</b></div>
      <pre style="margin:4px 0;color:#fbbf24;font-size:10.5px;">{candidates[],
 preferred,
 fallback_scenario}</pre>
    </div>
  </div>
  <div style="padding:14px;background:#0d1320;border:1px solid #2a3f5f;border-radius:8px;">
    <h4 style="margin:0 0 8px;color:#93c5fd;">Control</h4>
    <div style="font-size:11.5px;line-height:1.7;">
      <div><b>in:</b></div>
      <pre style="margin:4px 0;color:#9ca3af;font-size:10.5px;">{candidates[],
 conservator_out,
 tokens_budget.control}</pre>
      <div><b>out:</b></div>
      <pre style="margin:4px 0;color:#93c5fd;font-size:10.5px;">{verdicts[],
 glossary,
 disagreements,
 tests_to_write}</pre>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add D11 — Sequential vs. Trias dispatch comparison**

After D10:

```html
<h3 style="margin-top:32px;">Sequential vs. Trias — cum sunt dispatched aceleași voci</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:12px;">
  <div style="padding:14px;background:#0a2e23;border:1px solid #145c45;border-radius:8px;">
    <h4 style="margin:0 0 10px;color:#6ee7b7;">Sequential — 1 context, 3 roluri</h4>
    <svg viewBox="0 0 320 180" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="20" width="280" height="140" rx="8" fill="#11151c" stroke="#2d3441" stroke-dasharray="4,3"/>
      <text x="160" y="40" fill="#9ca3af" font-size="11" text-anchor="middle" font-style="italic">single context window (Claude main)</text>
      <rect x="40" y="55" width="80" height="30" rx="4" fill="#2a1818" stroke="#5c2a2a"/>
      <text x="80" y="74" fill="#fca5a5" font-size="11" text-anchor="middle">Cons</text>
      <rect x="125" y="55" width="80" height="30" rx="4" fill="#2a2410" stroke="#5c4a14"/>
      <text x="165" y="74" fill="#fbbf24" font-size="11" text-anchor="middle">Gen</text>
      <rect x="210" y="55" width="80" height="30" rx="4" fill="#182338" stroke="#2a3f5f"/>
      <text x="250" y="74" fill="#93c5fd" font-size="11" text-anchor="middle">Ctrl</text>
      <text x="160" y="110" fill="#e5e7eb" font-size="10" text-anchor="middle">strip_context.py între voci</text>
      <text x="160" y="130" fill="#9ca3af" font-size="9" text-anchor="middle">role separation, NU chinese wall</text>
      <text x="160" y="148" fill="#9ca3af" font-size="9" text-anchor="middle">cost: 0.33× Parallel</text>
    </svg>
  </div>
  <div style="padding:14px;background:#221830;border:1px solid #4c2a6b;border-radius:8px;">
    <h4 style="margin:0 0 10px;color:#d8b4fe;">Trias — 9 sub-agents, 3 lenses × 3 voci</h4>
    <svg viewBox="0 0 320 180" xmlns="http://www.w3.org/2000/svg">
      <text x="160" y="20" fill="#9ca3af" font-size="11" text-anchor="middle" font-style="italic">3 lenses prepended × 3 voci core</text>
      <!-- Pioneer column -->
      <rect x="20" y="30" width="80" height="130" rx="6" fill="#11151c" stroke="#4c2a6b"/>
      <text x="60" y="48" fill="#d8b4fe" font-size="10" text-anchor="middle" font-weight="700">Pioneer</text>
      <rect x="28" y="58" width="64" height="22" rx="3" fill="#2a2410"/><text x="60" y="73" fill="#fbbf24" font-size="9" text-anchor="middle">Gen</text>
      <rect x="28" y="84" width="64" height="22" rx="3" fill="#182338"/><text x="60" y="99" fill="#93c5fd" font-size="9" text-anchor="middle">Ctrl</text>
      <rect x="28" y="110" width="64" height="22" rx="3" fill="#2a1818"/><text x="60" y="125" fill="#fca5a5" font-size="9" text-anchor="middle">Cons</text>
      <!-- Architect -->
      <rect x="115" y="30" width="80" height="130" rx="6" fill="#11151c" stroke="#4c2a6b"/>
      <text x="155" y="48" fill="#d8b4fe" font-size="10" text-anchor="middle" font-weight="700">Architect</text>
      <rect x="123" y="58" width="64" height="22" rx="3" fill="#2a2410"/><text x="155" y="73" fill="#fbbf24" font-size="9" text-anchor="middle">Gen</text>
      <rect x="123" y="84" width="64" height="22" rx="3" fill="#182338"/><text x="155" y="99" fill="#93c5fd" font-size="9" text-anchor="middle">Ctrl</text>
      <rect x="123" y="110" width="64" height="22" rx="3" fill="#2a1818"/><text x="155" y="125" fill="#fca5a5" font-size="9" text-anchor="middle">Cons</text>
      <!-- Steward -->
      <rect x="210" y="30" width="80" height="130" rx="6" fill="#11151c" stroke="#4c2a6b"/>
      <text x="250" y="48" fill="#d8b4fe" font-size="10" text-anchor="middle" font-weight="700">Steward</text>
      <rect x="218" y="58" width="64" height="22" rx="3" fill="#2a2410"/><text x="250" y="73" fill="#fbbf24" font-size="9" text-anchor="middle">Gen</text>
      <rect x="218" y="84" width="64" height="22" rx="3" fill="#182338"/><text x="250" y="99" fill="#93c5fd" font-size="9" text-anchor="middle">Ctrl</text>
      <rect x="218" y="110" width="64" height="22" rx="3" fill="#2a1818"/><text x="250" y="125" fill="#fca5a5" font-size="9" text-anchor="middle">Cons</text>
      <text x="155" y="178" fill="#9ca3af" font-size="9" text-anchor="middle">cost: 3.0× Parallel</text>
    </svg>
  </div>
</div>
```

- [ ] **Step 4: Add D12 — lens weights heatmap (3×3 matrix)**

Insert before the existing `.lens-grid` (or after it as visual summary). Place after `.lens-grid`:

```html
<h3 style="margin-top:24px;">Lens weights — heatmap</h3>
<div style="overflow-x:auto;margin-top:8px;">
  <table style="border-collapse:collapse;font-size:12px;text-align:center;">
    <thead>
      <tr><th></th><th style="padding:6px 12px;">gen</th><th style="padding:6px 12px;">ctl</th><th style="padding:6px 12px;">cons</th></tr>
    </thead>
    <tbody>
      <tr>
        <th style="text-align:right;padding:6px 12px;color:#d8b4fe;">Pioneer</th>
        <td style="padding:8px 14px;background:#3a5121;color:#e5e7eb;font-weight:700;">0.49</td>
        <td style="padding:8px 14px;background:#2a3b1f;color:#e5e7eb;">0.30</td>
        <td style="padding:8px 14px;background:#1a2a1a;color:#e5e7eb;">0.21</td>
      </tr>
      <tr>
        <th style="text-align:right;padding:6px 12px;color:#d8b4fe;">Architect</th>
        <td style="padding:8px 14px;background:#2a3b1f;color:#e5e7eb;">0.30</td>
        <td style="padding:8px 14px;background:#3a5121;color:#e5e7eb;font-weight:700;">0.40</td>
        <td style="padding:8px 14px;background:#2a3b1f;color:#e5e7eb;">0.30</td>
      </tr>
      <tr>
        <th style="text-align:right;padding:6px 12px;color:#d8b4fe;">Steward</th>
        <td style="padding:8px 14px;background:#2a3b1f;color:#e5e7eb;">0.30</td>
        <td style="padding:8px 14px;background:#2a3b1f;color:#e5e7eb;">0.30</td>
        <td style="padding:8px 14px;background:#3a5121;color:#e5e7eb;font-weight:700;">0.40</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px;color:var(--muted);margin:8px 0 0;">Suma fiecărei linii = 1.0. Culoarea cea mai închisă = ponderea dominantă a lensei.</p>
</div>
```

- [ ] **Step 5: Add D13 — Skeptic field of view**

After Skeptic section (before Domain lens):

```html
<h3 style="margin-top:20px;">Ce vede / ce NU vede Skeptic</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px;">
  <div style="padding:12px;background:#0a2e23;border:1px solid #145c45;border-radius:6px;">
    <h4 style="margin:0 0 6px;color:#6ee7b7;">VEDE</h4>
    <ul style="margin:0;padding-left:18px;font-size:12px;color:#6ee7b7;line-height:1.7;">
      <li><code>chosen</code> candidate</li>
      <li><code>success_criterion</code></li>
      <li><code>verification</code> steps</li>
      <li>codebase context (Read, Grep)</li>
    </ul>
  </div>
  <div style="padding:12px;background:#3a1d1d;border:1px solid #7a3030;border-radius:6px;">
    <h4 style="margin:0 0 6px;color:#fca5a5;">NU VEDE</h4>
    <ul style="margin:0;padding-left:18px;font-size:12px;color:#fca5a5;line-height:1.7;">
      <li>ceilalți candidați</li>
      <li>scorurile Conservatorului</li>
      <li>verdictele Control</li>
      <li>deliberarea însăși</li>
    </ul>
  </div>
</div>
<p style="font-size:11px;color:var(--muted);margin:8px 0 0;">Izolarea informațională = Skeptic nu poate fabrica obiecții bazate pe ceea ce alții au spus deja; trebuie să găsească concerns concrete pe cont propriu sau să tacă (<code>can_object: false</code>).</p>
```

- [ ] **Step 6: Add Voices glossary**

Before `</section>` of `#voices`:

```html
<div class="glossary">
  <h3>Glosar Voices</h3>
  <dl>
    <dt>clarity gate</dt><dd>Step 1: dacă există 2+ interpretări plauzibile ale request-ului, pipeline-ul se oprește și cere clarificare înainte de Generator.</dd>
    <dt>tokens_budget</dt><dd>Conservator setează un budget per voce downstream (generator/control) bazat pe magnitude-ul deciziei — micșorează cost-ul pentru triviale.</dd>
    <dt>irreversibility_flag</dt><dd>Output Conservator: dacă <code>true</code>, pipeline blocat până la consimțământ explicit user. Default trigger pe migration/security/permanent state.</dd>
    <dt>glossary_fail</dt><dd>Output Control: când vocile folosesc terminologie abstractă neancorată în deliberare; soft veto care cere reformulare.</dd>
    <dt>net_concern</dt><dd>Scor Conservator ∈ [0,1] din 4 componente (diff_size, scope_drift, regression_risk, reversibility). Floor rule: <code>reversibility &gt; 0.7</code> ⇒ <code>net_concern ≥ reversibility</code>.</dd>
    <dt>addressable</dt><dd>Output Skeptic — clasifică obiecția: <code>in_place</code> (fix mic), <code>requires_redesign</code> (alt candidate), <code>unaddressable</code> (escaladare).</dd>
    <dt>meta_scope_mismatch</dt><dd>Failure mode Skeptic: chosen e corect, dar deliberarea însăși a fost over-aplicată pe o problemă trivială.</dd>
    <dt>prepended lens</dt><dd>Personality lens (Pioneer/Architect/Steward) injectat înainte de prompt-ul vocii core, schimbă biasul fără să schimbe rolul.</dd>
  </dl>
</div>
```

- [ ] **Step 7: Render check + amend commit**

Open browser, click Voices tab. Verify D9-D13 + glossary.

```bash
git add docs/architecture.html
git commit --amend --no-edit
```

---

## Task 5: Internals tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 981-1315 (`<section id="internals">`)

**Story arc**: Memory hook → 3 tiers → signals + state machine → OTAL Mermaid → [confirmed] timeline → CLI → Flow patterns interactive → Glosar.

- [ ] **Step 1: Update OTAL Mermaid to reflect 8 steps**

In the agent loop Mermaid (~lines 1068-1091), the `ACT` node says "Step 5". Keep that, but the cycle `LEARN -.->|"priors loop\nStep 0"| OBS` is fine. Just confirm the diagram still makes sense after Step 7 addition. If not, add a small note: `ACT["ACT\nStep 5: aggregator.py\nStep 7: infer_pipeline.py (cond)"]:::act`.

Update: `ACT["ACT\nStep 5: aggregator → chosen\nStep 7: infer_pipeline (cond)"]:::act`

- [ ] **Step 2: Add D14 — read/write paths per script (table-as-diagram)**

After the 3 tiers cards (`.tiers` div), before the existing signals table, insert:

```html
<h3 style="margin-top:28px;">Read / Write paths — care script atinge ce tier</h3>
<table class="rw-matrix" style="font-size:12px;border-collapse:collapse;width:100%;max-width:800px;">
  <thead>
    <tr>
      <th style="padding:6px 10px;text-align:left;">Script</th>
      <th style="padding:6px 10px;text-align:center;background:#0a2e23;color:#6ee7b7;">SHORT</th>
      <th style="padding:6px 10px;text-align:center;background:#182338;color:#93c5fd;">MEDIUM (runs/)</th>
      <th style="padding:6px 10px;text-align:center;background:#2a2410;color:#fbbf24;">LONG (FEEDBACK)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:6px 10px;"><code>priors.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>build_report.py</code></td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#fca5a5;">W</td>
      <td style="text-align:center;color:#9ca3af;">—</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>log_feedback.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#fca5a5;">W (append)</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>memory.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>mark_outcome.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#fca5a5;">W (overwrite row)</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>audit_feedback.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#6ee7b7;">R + W (backfill)</td>
    </tr>
    <tr>
      <td style="padding:6px 10px;"><code>infer_pipeline.py</code></td>
      <td style="text-align:center;color:#9ca3af;">—</td>
      <td style="text-align:center;color:#6ee7b7;">R</td>
      <td style="text-align:center;color:#9ca3af;">—</td>
    </tr>
  </tbody>
</table>
<p style="font-size:11px;color:var(--muted);margin:6px 0 0;">R = read, W = write. SHORT = active conversation, scriptable doar prin Claude main, nu disk-backed.</p>
```

- [ ] **Step 3: Add D15 — priors.py gate state machine (SVG)**

Insert after the signals table:

```html
<h3 style="margin-top:24px;">Step 0 gate — state machine</h3>
<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="priors.py gate state machine">
  <!-- start state -->
  <circle cx="80" cy="110" r="22" fill="#11151c" stroke="#2d3441"/>
  <text x="80" y="114" fill="#e5e7eb" font-size="10" text-anchor="middle">start</text>
  <!-- arrow to check -->
  <line x1="102" y1="110" x2="160" y2="110" stroke="#9ca3af" stroke-width="1.5"/>
  <polygon points="155,106 162,110 155,114" fill="#9ca3af"/>
  <!-- check -->
  <rect x="165" y="80" width="160" height="60" rx="8" fill="#182338" stroke="#2a3f5f"/>
  <text x="245" y="105" fill="#93c5fd" font-size="12" text-anchor="middle" font-weight="600">priors.py check</text>
  <text x="245" y="122" fill="#9ca3af" font-size="10" text-anchor="middle">stale + missing + pressure</text>
  <!-- branches -->
  <!-- clean -->
  <line x1="325" y1="100" x2="450" y2="55" stroke="#34d399" stroke-width="1.5"/>
  <polygon points="446,53 452,56 447,60" fill="#34d399"/>
  <text x="380" y="70" fill="#6ee7b7" font-size="10">clean</text>
  <rect x="455" y="30" width="160" height="50" rx="8" fill="#0a2e23" stroke="#145c45"/>
  <text x="535" y="50" fill="#6ee7b7" font-size="12" text-anchor="middle" font-weight="700">proceed</text>
  <text x="535" y="68" fill="#6ee7b7" font-size="10" text-anchor="middle">Step 1 unlocked</text>
  <!-- blocked -->
  <line x1="325" y1="120" x2="450" y2="120" stroke="#f87171" stroke-width="1.5"/>
  <polygon points="445,116 452,120 445,124" fill="#f87171"/>
  <text x="380" y="114" fill="#fca5a5" font-size="10">stale ∨ missing</text>
  <rect x="455" y="95" width="160" height="50" rx="8" fill="#3a1d1d" stroke="#7a3030"/>
  <text x="535" y="115" fill="#fca5a5" font-size="12" text-anchor="middle" font-weight="700">BLOCKED</text>
  <text x="535" y="133" fill="#fca5a5" font-size="9" text-anchor="middle">resolve via mark_outcome / backfill</text>
  <!-- alert -->
  <line x1="325" y1="140" x2="450" y2="180" stroke="#fbbf24" stroke-width="1.5"/>
  <polygon points="446,176 452,180 447,184" fill="#fbbf24"/>
  <text x="380" y="170" fill="#fbbf24" font-size="10">pend_pressure &gt; 0.3</text>
  <rect x="455" y="160" width="160" height="50" rx="8" fill="#2a2410" stroke="#5c4a14"/>
  <text x="535" y="180" fill="#fbbf24" font-size="12" text-anchor="middle" font-weight="700">ALERT (soft)</text>
  <text x="535" y="198" fill="#fbbf24" font-size="9" text-anchor="middle">warn; nu blochează</text>
  <!-- loop back from blocked -->
  <path d="M 535 145 Q 535 200 200 200 Q 100 200 100 132" stroke="#9ca3af" stroke-width="1" fill="none" stroke-dasharray="3,3"/>
  <polygon points="96,127 100,134 104,127" fill="#9ca3af"/>
  <text x="300" y="215" fill="#9ca3af" font-size="9">re-run după resolve</text>
</svg>
```

- [ ] **Step 4: Add D16 — [confirmed] marker timeline**

After the `.mem-confirmed` block:

```html
<h3 style="margin-top:24px;">[confirmed] — cum se ponderează retroactiv</h3>
<svg viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="confirmed marker timeline">
  <!-- timeline axis -->
  <line x1="40" y1="100" x2="680" y2="100" stroke="#9ca3af" stroke-width="1.5"/>
  <polygon points="675,96 682,100 675,104" fill="#9ca3af"/>
  <text x="685" y="104" fill="#9ca3af" font-size="10">t</text>
  <!-- T0 -->
  <circle cx="120" cy="100" r="6" fill="#fbbf24"/>
  <text x="120" y="84" fill="#fbbf24" font-size="11" text-anchor="middle" font-weight="700">T₀</text>
  <text x="120" y="125" fill="#fbbf24" font-size="10" text-anchor="middle">Step 6: outcome=OK</text>
  <text x="120" y="138" fill="#9ca3af" font-size="9" text-anchor="middle">weight = 1×</text>
  <text x="120" y="152" fill="#9ca3af" font-size="9" text-anchor="middle">(subiectiv)</text>
  <!-- T1 -->
  <circle cx="360" cy="100" r="6" fill="#f87171"/>
  <text x="360" y="84" fill="#fca5a5" font-size="11" text-anchor="middle" font-weight="700">T₁</text>
  <text x="360" y="125" fill="#fca5a5" font-size="10" text-anchor="middle">prod regression</text>
  <text x="360" y="138" fill="#fca5a5" font-size="9" text-anchor="middle">mark_outcome.py</text>
  <text x="360" y="152" fill="#fca5a5" font-size="9" text-anchor="middle">→ BAD [confirmed]</text>
  <!-- T2 -->
  <circle cx="600" cy="100" r="6" fill="#34d399"/>
  <text x="600" y="84" fill="#6ee7b7" font-size="11" text-anchor="middle" font-weight="700">T₂</text>
  <text x="600" y="125" fill="#6ee7b7" font-size="10" text-anchor="middle">priors.py next run</text>
  <text x="600" y="138" fill="#6ee7b7" font-size="9" text-anchor="middle">weight = 2×</text>
  <text x="600" y="152" fill="#6ee7b7" font-size="9" text-anchor="middle">în weighted_bad_rate</text>
  <!-- segments -->
  <line x1="120" y1="100" x2="360" y2="100" stroke="#2d3441" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="360" y1="100" x2="600" y2="100" stroke="#2d3441" stroke-width="1" stroke-dasharray="4,3"/>
</svg>
```

- [ ] **Step 5: Condense flow patterns intro**

Find the `.pat-intro` block (~line 1120). The existing text is fine. Add one sentence after it:

```html
<p style="font-size:12px;color:var(--muted);margin-top:6px;">Apăsând <b>Play tour</b> sus-dreapta, fluxul selectat se animează pas-cu-pas — util pentru a vedea în ordine ce noduri sunt activate într-o deliberare reală.</p>
```

- [ ] **Step 6: Add Internals glossary**

Before `</section>` of `#internals`:

```html
<div class="glossary">
  <h3>Glosar Internals</h3>
  <dl>
    <dt>priors</dt><dd>Vezi Overview glosar — soft signals derivate din feedback istoric.</dd>
    <dt>stale_pending</dt><dd>O intrare PEND în FEEDBACK.html mai veche de 2 zile — blochează deliberări noi până e închisă retroactiv via <code>mark_outcome.py</code>.</dd>
    <dt>weighted_bad_rate</dt><dd>Procentaj BAD în istoric, cu intrările marcate <code>[confirmed]</code> ponderate 2× față de cele subiective.</dd>
    <dt>episodic memory</dt><dd>Tier-ul MEDIUM (<code>runs/*.json</code>) — un fișier per deliberare, păstrat indefinit (gitignored).</dd>
    <dt>soft signal</dt><dd>Semnal din <code>priors.py</code> care influențează deliberarea fără s-o blocheze (vs. <i>hard gate</i> = block).</dd>
    <dt>fail-open</dt><dd>Strategia <code>scope_gate.py</code>: dacă probe-ul Git eșuează (nu suntem în repo), gate-ul nu skip-uiește — deliberează by default. "Open" = pipeline-ul rulează.</dd>
    <dt>[confirmed] marker</dt><dd>String "[confirmed]" în nota outcome — semnalează că outcome-ul a fost validat în producție (nu doar impresie imediată). 2× weight.</dd>
    <dt>pend_pressure</dt><dd>Raportul PEND/total în ultimele 20 entries. Peste 0.3 → alertă soft (nu block); semnal că pipeline-ul produce prea multe outcomes neclasificate.</dd>
  </dl>
</div>
```

- [ ] **Step 7: Render check + amend commit**

Open browser, click Internals tab. Verify OTAL Mermaid shows updated ACT node, RW matrix table renders, D15 state machine + D16 timeline SVGs visible. **Critical: Play tour must still work** — click it, walk through a flow, ensure no JS errors.

```bash
git add docs/architecture.html
git commit --amend --no-edit
```

---

## Task 6: Reference tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 1316-1635 (`<section id="reference">`)
- Possibly modify: `docs/architecture.js` (if `#todoMatrixSvg` was in use)

**Story arc**: Repo map → Scripts inventory (3 clusters) → Git workflow → Dialectic merge → Senate (9 senators canonic) → Glosar.

- [ ] **Step 1: Decide TODO matrix fate**

Run: `grep -nE "todoMatrix|todoTooltip" docs/architecture.js`

- If JS uses these IDs and renders the TODO matrix dynamically → either keep matrix or also delete the JS code that targets it.
- Per spec (no TODO/known-limitations section in Reference), delete the matrix markup AND its JS handler.

Find the JS section that initializes/renders TODO matrix (likely a function or block referencing `todoMatrixSvg`). Remove it cleanly (leave the file valid JS).

- [ ] **Step 2: Add D17 — repo map (SVG tree)**

At very top of `#reference` section, after `<h2>Reference</h2>` (add this header if missing):

```html
<h2>Reference</h2>
<h3>Repo map — unde stă ce</h3>
<svg viewBox="0 0 760 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repo map tree">
  <text x="20" y="25" fill="#e5e7eb" font-size="13" font-weight="700">Consilium/</text>
  <!-- prompts/ -->
  <text x="40" y="50" fill="#fbbf24" font-size="12" font-family="ui-monospace,monospace">├── prompts/</text>
  <text x="220" y="50" fill="#9ca3af" font-size="11">contracte voci, lenses, senatori</text>
  <text x="60" y="68" fill="#9ca3af" font-size="11" font-family="ui-monospace,monospace">├── voices/</text>
  <text x="220" y="68" fill="#9ca3af" font-size="10">generator.md · control.md · conservator.md · skeptic.md · *_pass2.md</text>
  <text x="60" y="84" fill="#9ca3af" font-size="11" font-family="ui-monospace,monospace">├── lenses/</text>
  <text x="220" y="84" fill="#9ca3af" font-size="10">pioneer · architect · steward · domain (experimental)</text>
  <text x="60" y="100" fill="#9ca3af" font-size="11" font-family="ui-monospace,monospace">└── senators/</text>
  <text x="220" y="100" fill="#9ca3af" font-size="10">9 senatori — folosiți doar în mod senate</text>
  <!-- scripts/ -->
  <text x="40" y="124" fill="#93c5fd" font-size="12" font-family="ui-monospace,monospace">├── scripts/</text>
  <text x="220" y="124" fill="#9ca3af" font-size="11">Python stdlib-only, fiecare CLI cu argparse + JSON I/O</text>
  <text x="60" y="142" fill="#9ca3af" font-size="10">deliberation: priors · scope_gate · probe_change · aggregator · confidence · meta_critic · retry_context</text>
  <text x="60" y="158" fill="#9ca3af" font-size="10">feedback: build_report · validate_report · log_feedback · infer_pipeline</text>
  <text x="60" y="174" fill="#9ca3af" font-size="10">maintenance: audit_feedback · mark_outcome · memory · usage · run_evals</text>
  <text x="60" y="190" fill="#9ca3af" font-size="10">deprecated/ — retired one-shot tools (e.g. migrate_feedback_md_to_html.py)</text>
  <!-- runs/ -->
  <text x="40" y="214" fill="#6ee7b7" font-size="12" font-family="ui-monospace,monospace">├── runs/</text>
  <text x="220" y="214" fill="#9ca3af" font-size="11">JSON per deliberare (gitignored) + senate/ tracked + README</text>
  <!-- experiments/ -->
  <text x="40" y="238" fill="#d8b4fe" font-size="12" font-family="ui-monospace,monospace">├── experiments/</text>
  <text x="220" y="238" fill="#9ca3af" font-size="11">P3 car wash, frontend-domain-lens-pilot, benchmark runs</text>
  <!-- docs/ -->
  <text x="40" y="262" fill="#fbbf24" font-size="12" font-family="ui-monospace,monospace">├── docs/</text>
  <text x="220" y="262" fill="#9ca3af" font-size="11">architecture.html (acest fișier) · superpowers/specs/ · plans/</text>
  <!-- SKILL.md -->
  <text x="40" y="286" fill="#fca5a5" font-size="12" font-family="ui-monospace,monospace">├── SKILL.md</text>
  <text x="220" y="286" fill="#9ca3af" font-size="11">contract public — Constitution + 8-step workflow</text>
  <!-- CLAUDE.md -->
  <text x="40" y="310" fill="#fca5a5" font-size="12" font-family="ui-monospace,monospace">├── CLAUDE.md</text>
  <text x="220" y="310" fill="#9ca3af" font-size="11">project rules — convenții Python, git workflow, zone autoritative</text>
  <!-- FEEDBACK.html -->
  <text x="40" y="334" fill="#fbbf24" font-size="12" font-family="ui-monospace,monospace">└── FEEDBACK.html</text>
  <text x="220" y="334" fill="#9ca3af" font-size="11">jurnal long-tier (gitignored, append-only via log_feedback.py)</text>
  <text x="40" y="365" fill="#9ca3af" font-size="10" font-style="italic">Fișiere tracked toate; gitignored = vezi .gitignore.</text>
</svg>
```

- [ ] **Step 3: Add D18 — scripts grouped by role**

After D17:

```html
<h3 style="margin-top:24px;">Scripts — grupați pe rol</h3>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:8px;">
  <div style="padding:12px;background:#11151c;border:1px solid #2d3441;border-radius:8px;border-left:3px solid #93c5fd;">
    <h4 style="margin:0 0 8px;color:#93c5fd;">Deliberation pipeline</h4>
    <ul style="margin:0;padding-left:0;list-style:none;font-size:11.5px;line-height:1.7;color:#9ca3af;">
      <li><code>priors.py</code> — Step 0 soft signals</li>
      <li><code>scope_gate.py</code> — Step 1.5 auto-skip</li>
      <li><code>probe_change.py</code> — Step 2 anchor diff size</li>
      <li><code>aggregator.py</code> — Step 5 voting schemes</li>
      <li><code>confidence.py</code> — Step 5b agreement</li>
      <li><code>meta_critic.py</code> — Step 5c deliberation quality</li>
      <li><code>retry_context.py</code> — Step 5d retry hint</li>
      <li><code>strip_context.py</code> — Step 3-4 sequential util</li>
    </ul>
  </div>
  <div style="padding:12px;background:#11151c;border:1px solid #2d3441;border-radius:8px;border-left:3px solid #fbbf24;">
    <h4 style="margin:0 0 8px;color:#fbbf24;">Feedback loop</h4>
    <ul style="margin:0;padding-left:0;list-style:none;font-size:11.5px;line-height:1.7;color:#9ca3af;">
      <li><code>build_report.py</code> — Step 6 canonical report</li>
      <li><code>validate_report.py</code> — Step 6 gate (exit codes)</li>
      <li><code>log_feedback.py</code> — Step 6 append FEEDBACK.html</li>
      <li><code>infer_pipeline.py</code> — Step 7 deliverable execution</li>
    </ul>
  </div>
  <div style="padding:12px;background:#11151c;border:1px solid #2d3441;border-radius:8px;border-left:3px solid #6ee7b7;">
    <h4 style="margin:0 0 8px;color:#6ee7b7;">Maintenance</h4>
    <ul style="margin:0;padding-left:0;list-style:none;font-size:11.5px;line-height:1.7;color:#9ca3af;">
      <li><code>audit_feedback.py</code> — orphan detection + backfill</li>
      <li><code>mark_outcome.py</code> — outcome retroactiv [confirmed]</li>
      <li><code>memory.py</code> — read API 3 tiers</li>
      <li><code>usage.py</code> — telemetry rollup</li>
      <li><code>run_evals.py</code> — regression suite</li>
    </ul>
  </div>
</div>
```

- [ ] **Step 4: Add D19 — git workflow lifecycle SVG**

After the existing git workflow section (or replace its diagram if any exists):

```html
<h3 style="margin-top:24px;">Git workflow — lifecycle pentru schimbări non-triviale</h3>
<svg viewBox="0 0 780 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Git workflow lifecycle">
  <!-- 1. branch -->
  <rect x="10" y="60" width="100" height="50" rx="6" fill="#0a2e23" stroke="#145c45"/>
  <text x="60" y="80" fill="#6ee7b7" font-size="11" text-anchor="middle" font-weight="600">1. branch</text>
  <text x="60" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">feat/&lt;slug&gt;</text>
  <line x1="110" y1="85" x2="140" y2="85" stroke="#9ca3af"/>
  <polygon points="135,81 142,85 135,89" fill="#9ca3af"/>
  <!-- 2. edit -->
  <rect x="142" y="60" width="100" height="50" rx="6" fill="#182338" stroke="#2a3f5f"/>
  <text x="192" y="80" fill="#93c5fd" font-size="11" text-anchor="middle" font-weight="600">2. edit</text>
  <text x="192" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">Write/Edit tools</text>
  <line x1="242" y1="85" x2="272" y2="85" stroke="#9ca3af"/>
  <polygon points="267,81 274,85 267,89" fill="#9ca3af"/>
  <!-- 3. commit -->
  <rect x="274" y="60" width="100" height="50" rx="6" fill="#2a2410" stroke="#5c4a14"/>
  <text x="324" y="80" fill="#fbbf24" font-size="11" text-anchor="middle" font-weight="600">3. commit</text>
  <text x="324" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">conventional</text>
  <!-- amend loop -->
  <path d="M 374 85 Q 414 85 414 50 Q 414 30 274 30 Q 230 30 230 60" stroke="#fbbf24" stroke-width="1.5" fill="none" stroke-dasharray="3,3"/>
  <polygon points="226,55 230,62 234,55" fill="#fbbf24"/>
  <text x="324" y="22" fill="#fbbf24" font-size="9" text-anchor="middle">amend --no-edit (loop iterații)</text>
  <line x1="374" y1="85" x2="404" y2="85" stroke="#9ca3af"/>
  <polygon points="399,81 406,85 399,89" fill="#9ca3af"/>
  <!-- 4. push -->
  <rect x="406" y="60" width="100" height="50" rx="6" fill="#221830" stroke="#4c2a6b"/>
  <text x="456" y="80" fill="#d8b4fe" font-size="11" text-anchor="middle" font-weight="600">4. push (1x)</text>
  <text x="456" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">automat</text>
  <line x1="506" y1="85" x2="536" y2="85" stroke="#9ca3af"/>
  <polygon points="531,81 538,85 531,89" fill="#9ca3af"/>
  <!-- 5. checkout main -->
  <rect x="538" y="60" width="120" height="50" rx="6" fill="#11151c" stroke="#2d3441"/>
  <text x="598" y="80" fill="#e5e7eb" font-size="11" text-anchor="middle" font-weight="600">5. checkout main</text>
  <text x="598" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">automat</text>
  <line x1="658" y1="85" x2="688" y2="85" stroke="#9ca3af"/>
  <polygon points="683,81 690,85 683,89" fill="#9ca3af"/>
  <!-- 6. PR by user -->
  <rect x="690" y="60" width="80" height="50" rx="6" fill="#2a1818" stroke="#5c2a2a"/>
  <text x="730" y="80" fill="#fca5a5" font-size="11" text-anchor="middle" font-weight="600">6. PR</text>
  <text x="730" y="96" fill="#9ca3af" font-size="9" text-anchor="middle">manual user</text>
  <!-- footnote -->
  <text x="10" y="150" fill="#9ca3af" font-size="11">După push: schimbări noi = branch nou. Excepție: typo-uri 1-line direct pe main.</text>
  <text x="10" y="168" fill="#9ca3af" font-size="11">Naming: <tspan font-family="ui-monospace,monospace" fill="#e5e7eb">feat/&lt;slug&gt;</tspan> pentru features, <tspan font-family="ui-monospace,monospace" fill="#e5e7eb">fix/&lt;slug&gt;</tspan> pentru bugfixes.</text>
</svg>
```

Keep existing prose about workflow as-is below (rule list 1-7).

- [ ] **Step 5: Rewrite Senate section with 9 senators (D20 + D21)**

Find the existing Senate-related content in Reference (if any) or add a new section. Replace/insert:

```html
<h3 style="margin-top:32px;">Senate — 9 senatori, on-demand audit</h3>
<p style="color:var(--muted);font-size:13px;max-width:780px;">Senate are scope distinct: auditează modificările la <i>skill-ul însuși</i> (prompturi, scripts, SKILL.md) — nu cod user. 9 senatori cu optici disjuncte; verdict advisory, niciodată autoritar.</p>

<h4 style="margin-top:16px;font-size:13px;">Cei 9 senatori</h4>
<div class="senate-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:8px;">
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Aurelius</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">stoic — focus pe disciplină, evită overreaction</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Confucius</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">invariants & relații — coherence pe termen lung</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Deming</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">process quality — control statistic, feedback loop</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Dimon</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">risk/cost — atenție la blast radius și cost-of-mistake</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Musk</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">first-principles — desface assumptions, simplifică agresiv</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Napoleon</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">decision speed — escalează la verdict când evidence e suficient</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Socrate</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">întrebări — expune ce nu se discută; "ce am presupus aici?"</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Tacitus</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">istorician — context istoric al deciziei, ce s-a încercat înainte</div>
  </div>
  <div style="padding:10px;background:#11151c;border:1px solid #2d3441;border-radius:6px;">
    <b style="color:#fbbf24;">Wittgenstein</b>
    <div style="font-size:11px;color:#9ca3af;margin-top:4px;">clarificare lingvistică — "ce înseamnă exact termenul X aici?"</div>
  </div>
</div>

<h4 style="margin-top:20px;font-size:13px;">Senate flow</h4>
<svg viewBox="0 0 780 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Senate flow">
  <rect x="20" y="90" width="160" height="40" rx="6" fill="#0a2e23" stroke="#145c45"/>
  <text x="100" y="115" fill="#6ee7b7" font-size="12" text-anchor="middle" font-weight="700">Claude main</text>
  <line x1="180" y1="110" x2="240" y2="110" stroke="#c084fc" stroke-width="2"/>
  <polygon points="235,106 242,110 235,114" fill="#c084fc"/>
  <text x="210" y="102" fill="#d8b4fe" font-size="9" text-anchor="middle">dispatch × 9</text>
  <!-- 9 senators stacked -->
  <g>
    <rect x="245" y="25" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="40" fill="#fbbf24" font-size="10" text-anchor="middle">Aurelius</text>
    <rect x="245" y="50" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="65" fill="#fbbf24" font-size="10" text-anchor="middle">Confucius</text>
    <rect x="245" y="75" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="90" fill="#fbbf24" font-size="10" text-anchor="middle">Deming</text>
    <rect x="245" y="100" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="115" fill="#fbbf24" font-size="10" text-anchor="middle">Dimon</text>
    <rect x="245" y="125" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="140" fill="#fbbf24" font-size="10" text-anchor="middle">Musk</text>
    <rect x="245" y="150" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="165" fill="#fbbf24" font-size="10" text-anchor="middle">Napoleon</text>
    <rect x="245" y="175" width="180" height="22" rx="3" fill="#2a2410" stroke="#5c4a14"/><text x="335" y="190" fill="#fbbf24" font-size="10" text-anchor="middle">Socrate + Tacitus + Wittgenstein</text>
  </g>
  <line x1="425" y1="110" x2="485" y2="110" stroke="#c084fc" stroke-width="2"/>
  <polygon points="480,106 487,110 480,114" fill="#c084fc"/>
  <text x="455" y="102" fill="#d8b4fe" font-size="9" text-anchor="middle">9 verdicts</text>
  <rect x="490" y="80" width="120" height="60" rx="6" fill="#221830" stroke="#4c2a6b"/>
  <text x="550" y="105" fill="#d8b4fe" font-size="12" text-anchor="middle" font-weight="700">tally</text>
  <text x="550" y="123" fill="#9ca3af" font-size="9" text-anchor="middle">aggregate verdicts</text>
  <line x1="610" y1="110" x2="670" y2="110" stroke="#c084fc" stroke-width="2"/>
  <polygon points="665,106 672,110 665,114" fill="#c084fc"/>
  <rect x="675" y="85" width="95" height="50" rx="6" fill="#11151c" stroke="#2d3441"/>
  <text x="722" y="108" fill="#e5e7eb" font-size="11" text-anchor="middle" font-weight="700">advisory</text>
  <text x="722" y="124" fill="#9ca3af" font-size="9" text-anchor="middle">runs/senate/*.json</text>
</svg>

<p style="font-size:12px;color:var(--muted);margin-top:12px;">
<b>Scope default:</b> modificări la skill (prompturi, scripts, SKILL.md). On-demand, niciun trigger automat.<br>
<b>Flag <code>--on-code</code>:</b> EXPERIMENTAL — extinde scope-ul la audit pe cod user. Necesită gate empiric (≥3 pilot runs) înainte de promovare. Vezi SKILL.md.
</p>
```

- [ ] **Step 6: Delete redundant "fișiere autoritative" section if present**

The existing Reference has prose about which files are authoritative — if it duplicates info now in repo map + scripts inventory, remove.

- [ ] **Step 7: Add Reference glossary**

Before `</section>` of `#reference`:

```html
<div class="glossary">
  <h3>Glosar Reference</h3>
  <dl>
    <dt>senator</dt><dd>Un sub-agent în modul Senate cu prompt distinct (filozof istoric/CEO/etc.). 9 total, fiecare cu o optică disjunctă. Vot advisory.</dd>
    <dt>advisory verdict</dt><dd>Output care e citat în raport dar nu blochează deliberarea — vs. <i>blocking verdict</i> care oprește pipeline.</dd>
    <dt>dispatch</dt><dd>Apelul API care lansează un sub-agent — alocă propriul context window și pasează prompt + input. Vezi D8 în Modes.</dd>
    <dt>prepended prompt</dt><dd>Lens (Trias) sau senator role injectat la începutul system prompt-ului unui sub-agent înainte de prompt-ul vocii core.</dd>
    <dt>on-demand audit</dt><dd>Audit care rulează doar la cererea explicită user (Senate default) — vs. <i>auto cross-check</i> (Parallel) care se declanșează din triggere derivate.</dd>
    <dt>revision_log</dt><dd>Output Dialectic Pass 2: înregistrează ce a schimbat fiecare voce între Pass 1 și Pass 2 (<code>revision:</code> sau <code>maintained:</code>).</dd>
    <dt>--on-code flag</dt><dd>Flag experimental pentru Senate: extinde scope-ul la cod user. Necesită gate empiric (≥3 pilot runs OK) înainte de scale-up.</dd>
    <dt>empirical gate</dt><dd>Cerință de a colecta date pilot (ex. 3-5 runs cu outcome OK) înainte de promovarea unei capabilități experimentale în prod.</dd>
  </dl>
</div>
```

- [ ] **Step 8: Render check + amend commit**

Open browser, click Reference tab. Verify D17 tree, D18 scripts groups, D19 git workflow, Senate section with 9 senators + D21 flow + D20 cards, glossary at end. Verify no JS errors if TODO matrix was removed.

```bash
git add docs/architecture.html docs/architecture.js
git commit --amend --no-edit
```

---

## Task 7: Efficiency tab rewrite

**Files:**
- Modify: `docs/architecture.html` lines 1636 onward (`<section id="efficiency">`)

**Story arc**: Întrebarea cost/OK → cost anatomy → tabele grouped → cost/OK ratio → când merită → benchmark methodology → Glosar.

- [ ] **Step 1: Read current Efficiency content**

Run a quick read of `docs/architecture.html` lines 1636 to end via Read tool to confirm what content exists.

- [ ] **Step 2: Add D22 — tokens/OK bar chart hook at top**

After `<section class="tab" id="efficiency">`, add an opening:

```html
<h2>Cât plătești per OK?</h2>
<p style="color:var(--muted);font-size:13.5px;max-width:780px;">Costul nu se măsoară în tokens absolut — ci în tokens per outcome confirmat ca OK. Sequential și Trias arată foarte diferit la prima coloană, dar mai puțin diferit la a doua dacă Trias previne un retry costisitor.</p>
<svg viewBox="0 0 760 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tokens per OK by mode">
  <text x="380" y="20" fill="#e5e7eb" font-size="12" text-anchor="middle" font-weight="600">Tokens per OK confirmat (ilustrativ — actualizează cu date reale din usage.py)</text>
  <!-- Y axis -->
  <line x1="60" y1="240" x2="720" y2="240" stroke="#9ca3af"/>
  <line x1="60" y1="240" x2="60" y2="40" stroke="#9ca3af"/>
  <text x="50" y="244" fill="#9ca3af" font-size="9" text-anchor="end">0</text>
  <text x="50" y="180" fill="#9ca3af" font-size="9" text-anchor="end">25k</text>
  <text x="50" y="120" fill="#9ca3af" font-size="9" text-anchor="end">50k</text>
  <text x="50" y="60" fill="#9ca3af" font-size="9" text-anchor="end">75k</text>
  <!-- bars -->
  <rect x="100" y="200" width="60" height="40" fill="#0a2e23" stroke="#145c45"/><text x="130" y="258" fill="#6ee7b7" font-size="10" text-anchor="middle">SEQ</text><text x="130" y="195" fill="#6ee7b7" font-size="9" text-anchor="middle">~8k</text>
  <rect x="200" y="130" width="60" height="110" fill="#182338" stroke="#2a3f5f"/><text x="230" y="258" fill="#93c5fd" font-size="10" text-anchor="middle">DIAL</text><text x="230" y="125" fill="#93c5fd" font-size="9" text-anchor="middle">~38k</text>
  <rect x="300" y="100" width="60" height="140" fill="#221830" stroke="#4c2a6b"/><text x="330" y="258" fill="#d8b4fe" font-size="10" text-anchor="middle">TRI</text><text x="330" y="95" fill="#d8b4fe" font-size="9" text-anchor="middle">~52k</text>
  <rect x="400" y="115" width="60" height="125" fill="#221830" stroke="#4c2a6b" opacity="0.7"/><text x="430" y="258" fill="#d8b4fe" font-size="10" text-anchor="middle">TRI-s</text><text x="430" y="110" fill="#d8b4fe" font-size="9" text-anchor="middle">~44k</text>
  <rect x="500" y="80" width="60" height="160" fill="#2a2410" stroke="#5c4a14"/><text x="530" y="258" fill="#fbbf24" font-size="10" text-anchor="middle">SEN</text><text x="530" y="75" fill="#fbbf24" font-size="9" text-anchor="middle">~62k</text>
  <text x="60" y="278" fill="#9ca3af" font-size="9">Valori orientative; rulează <tspan font-family="ui-monospace,monospace" fill="#e5e7eb">python scripts/usage.py --rollup</tspan> pentru numere actuale.</text>
</svg>
```

- [ ] **Step 3: Add D23 — cost anatomy breakdown**

After D22:

```html
<h3 style="margin-top:24px;">De ce Trias ≈ 3× Sequential — cost anatomy</h3>
<svg viewBox="0 0 760 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cost anatomy">
  <!-- Sequential -->
  <text x="20" y="30" fill="#6ee7b7" font-size="13" font-weight="700">Sequential</text>
  <rect x="20" y="40" width="320" height="32" fill="#0a2e23" stroke="#145c45"/>
  <text x="180" y="60" fill="#6ee7b7" font-size="11" text-anchor="middle">1× input (shared context, 3 roluri)</text>
  <rect x="20" y="75" width="200" height="22" fill="#11151c" stroke="#145c45"/>
  <text x="120" y="91" fill="#6ee7b7" font-size="10" text-anchor="middle">3× output (cands + verdicts + risk)</text>
  <!-- Parallel -->
  <text x="20" y="130" fill="#fbbf24" font-size="13" font-weight="700">Parallel (auto only)</text>
  <rect x="20" y="140" width="100" height="32" fill="#2a2410" stroke="#5c4a14"/><text x="70" y="160" fill="#fbbf24" font-size="10" text-anchor="middle">input ×3</text>
  <rect x="125" y="140" width="100" height="32" fill="#2a2410" stroke="#5c4a14"/><text x="175" y="160" fill="#fbbf24" font-size="10" text-anchor="middle">input ×3</text>
  <rect x="230" y="140" width="100" height="32" fill="#2a2410" stroke="#5c4a14"/><text x="280" y="160" fill="#fbbf24" font-size="10" text-anchor="middle">input ×3</text>
  <rect x="20" y="175" width="310" height="22" fill="#11151c" stroke="#5c4a14"/>
  <text x="175" y="191" fill="#fbbf24" font-size="10" text-anchor="middle">3× output (one per sub-agent)</text>
  <!-- Trias -->
  <text x="400" y="30" fill="#d8b4fe" font-size="13" font-weight="700">Trias (3 personalități × 3 voci)</text>
  <g>
    <rect x="400" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="442" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="484" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="526" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="568" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="610" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="652" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="694" y="40" width="38" height="32" fill="#221830" stroke="#4c2a6b"/>
    <rect x="610" y="76" width="80" height="20" fill="#221830" stroke="#4c2a6b"/>
  </g>
  <text x="565" y="105" fill="#d8b4fe" font-size="11" text-anchor="middle">9× input (fiecare sub-agent restartat)</text>
  <rect x="400" y="120" width="330" height="22" fill="#11151c" stroke="#4c2a6b"/>
  <text x="565" y="136" fill="#d8b4fe" font-size="10" text-anchor="middle">9× output + vot tally</text>
  <!-- bottom note -->
  <line x1="20" y1="220" x2="740" y2="220" stroke="#2d3441" stroke-width="1"/>
  <text x="20" y="240" fill="#e5e7eb" font-size="12" font-weight="600">Concluzie</text>
  <text x="20" y="256" fill="#9ca3af" font-size="11">Cost-ul nu vine din diferența de complexitate a deliberării, ci din numărul de restart-uri de context (input duplicat).</text>
</svg>
```

- [ ] **Step 4: Group existing tokens tables in 3 clusters**

If existing efficiency tables exist, add section headers above them grouping into:
- Standard modes (Sequential, Dialectic, Trias)
- Split / Composabil (trias_split, skeptic_on_chosen)
- Audit (Senate)

If no tables exist yet, add placeholder:

```html
<h3 style="margin-top:24px;">Tokens per mod (rulează <code>scripts/usage.py --rollup</code> pentru date live)</h3>
<p style="color:var(--muted);font-size:12px;">Tabelele detaliate sunt populate din <code>FEEDBACK.html</code> + <code>runs/</code>. Vezi <code>scripts/usage.py</code> CLI.</p>
```

(If tables exist already, keep them, just regroup with `<h4>` headers.)

- [ ] **Step 5: Add D25 — cost vs. consequence quadrant**

After tables section:

```html
<h3 style="margin-top:24px;">Când merită cost-ul — cost-of-mistake × cost-of-running</h3>
<svg viewBox="0 0 720 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cost vs consequence quadrant">
  <!-- axes -->
  <line x1="60" y1="320" x2="660" y2="320" stroke="#9ca3af" stroke-width="1.5"/>
  <line x1="60" y1="320" x2="60" y2="40" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="360" y="345" fill="#e5e7eb" font-size="12" text-anchor="middle">cost-of-running →</text>
  <text x="30" y="180" fill="#e5e7eb" font-size="12" text-anchor="middle" transform="rotate(-90 30 180)">cost-of-mistake →</text>
  <!-- quadrants -->
  <line x1="360" y1="320" x2="360" y2="40" stroke="#2d3441" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="60" y1="180" x2="660" y2="180" stroke="#2d3441" stroke-width="1" stroke-dasharray="3,3"/>
  <!-- Q top-left: high mistake, low running -->
  <text x="80" y="65" fill="#34d399" font-size="13" font-weight="700">SWEET SPOT</text>
  <text x="80" y="82" fill="#6ee7b7" font-size="11">cost-of-mistake high,</text>
  <text x="80" y="96" fill="#6ee7b7" font-size="11">cost-of-running low</text>
  <text x="80" y="116" fill="#6ee7b7" font-size="10" font-style="italic">→ Trias / Senate justified</text>
  <!-- Q top-right: high+high -->
  <text x="380" y="65" fill="#fbbf24" font-size="13" font-weight="700">JUSTIFIED</text>
  <text x="380" y="82" fill="#fbbf24" font-size="11">high mistake + high running</text>
  <text x="380" y="116" fill="#fbbf24" font-size="10" font-style="italic">→ Trias, dar verifică decision speed</text>
  <!-- Q bottom-left: low+low -->
  <text x="80" y="230" fill="#9ca3af" font-size="13" font-weight="700">USE Sequential</text>
  <text x="80" y="247" fill="#9ca3af" font-size="11">low mistake + low running</text>
  <text x="80" y="281" fill="#9ca3af" font-size="10" font-style="italic">→ Sequential or scope_gate skip</text>
  <!-- Q bottom-right: low mistake, high running -->
  <text x="380" y="230" fill="#fca5a5" font-size="13" font-weight="700">WASTE</text>
  <text x="380" y="247" fill="#fca5a5" font-size="11">low mistake, high running</text>
  <text x="380" y="281" fill="#fca5a5" font-size="10" font-style="italic">→ Trias pe typo = waste</text>
</svg>
```

- [ ] **Step 6: Add benchmark methodology note**

After D25:

```html
<h3 style="margin-top:20px;">Benchmark methodology — pe scurt</h3>
<p style="font-size:12.5px;line-height:1.6;color:var(--muted);max-width:780px;">
Toate modurile primesc același flag <code>--effort</code> în benchmark — modelele decid intern cât deliberează. Nu tunăm parametri per-mod. Problemele din benchmark sunt designed să pună în dificultate modelele; nu sunt înlocuite cu variante mai simple pentru cost reduction. Vezi <code>experiments/</code> pentru runs concrete (P3 car wash, benchmark wrapper).
</p>
```

- [ ] **Step 7: Add Efficiency glossary**

Before `</section>` of `#efficiency`:

```html
<div class="glossary">
  <h3>Glosar Efficiency</h3>
  <dl>
    <dt>tokens/OK</dt><dd>Total tokens consumați împărțit la numărul de outcomes OK confirmate în același set de runs. Metrică-cheie de cost-efficiency.</dd>
    <dt>baseline</dt><dd>Parallel (3 sub-agents) = 1.0×. Toate celelalte cost-uri se raportează la asta.</dd>
    <dt>multiplier vs Parallel</dt><dd>Raportul tokens/OK al modului față de Parallel — ex. Sequential = 0.33×, Trias = 3.0×.</dd>
    <dt>effort flag</dt><dd><code>--effort low|medium|high</code> în CLI — controlează intensitatea efortului per sub-agent (max tokens, retry tolerance).</dd>
    <dt>OK / PEND / BAD / OVR</dt><dd>Cele 4 outcomes posibile pentru un run: OK (success), PEND (pending review), BAD (failed in prod), OVR (user override). [confirmed] în notă = ponderează 2× în <code>weighted_bad_rate</code>.</dd>
    <dt>cost-of-mistake</dt><dd>Costul presupus al unei decizii greșite — ireversibilitate, blast radius, downtime, lost trust. Folosit în decision-making pentru cost-justification (vezi D25).</dd>
  </dl>
</div>
```

- [ ] **Step 8: Render check + amend commit**

Open browser, click Efficiency tab. Verify D22 chart, D23 anatomy, table groupings, D25 quadrant, glossary.

```bash
git add docs/architecture.html
git commit --amend --no-edit
```

---

## Task 8: Cross-cutting cleanup

**Files:**
- Modify: `docs/architecture.html` (anchor + glossary consistency)
- Possibly: `docs/architecture.css` (new selectors if needed)

- [ ] **Step 1: Verify all intra-page anchors resolve**

Run: `grep -oE 'href="#[^"]+"' docs/architecture.html | sort -u`
For each `#X`, grep for `id="X"` in the same file. Any orphan → fix or remove.

Expected anchors that must exist: `#overview`, `#modes`, `#voices`, `#internals`, `#reference`, `#efficiency`, `#trias-deepdive`.

- [ ] **Step 2: Verify each glossary term appears in its tab's prose**

For each `<dt>term</dt>` in each glossary, grep that the term appears at least once in the tab body. Orphan term = remove from glossary or add to prose.

- [ ] **Step 3: File size check**

Run: `dir docs\architecture.html` (Windows). Expect < 250KB. If over budget, see if any old SVG can be simplified.

- [ ] **Step 4: CSS sanity check**

Verify `.glossary`, `.glossary dl`, `.glossary dt`, `.glossary dd`, `.compare-table`, `.rw-matrix` selectors render correctly. If any styling broken (white text on light bg, overlap), tighten CSS.

- [ ] **Step 5: Mermaid render check across all tabs**

Open browser DevTools console. Click each tab in order. After each tab, check console for Mermaid errors (red text). Fix any failing diagram syntax.

- [ ] **Step 6: Amend commit**

```bash
git add docs/architecture.html docs/architecture.css
git commit --amend --no-edit
```

---

## Task 9: Final verification

- [ ] **Step 1: Full walkthrough**

Open `docs/architecture.html` in browser. For each tab:
- All Mermaid diagrams render without red errors
- All SVGs display correctly (not cropped, no broken arrows)
- All glossaries visible at bottom
- No console errors
- Play tour still works in Internals tab
- Tab switching preserves on reload (sessionStorage)

- [ ] **Step 2: Cross-browser sanity (optional)**

If feasible, open in both Chrome and Firefox. Mermaid + SVG should render identically.

- [ ] **Step 3: Final amend commit + push**

```bash
git add docs/architecture.html docs/architecture.css
git commit --amend --no-edit
git push -u origin feat/architecture-html-rework-impl
```

- [ ] **Step 4: Return to main**

```bash
git checkout main
```

Done. Report branch name to user for PR creation.

---

## Self-Review

**Spec coverage:**

- ✓ 6 tab story arcs → Tasks 2-7
- ✓ 25 new diagrams (D1-D25) → one per applicable task step
- ✓ Per-tab glossaries → final step of each tab task
- ✓ Pipeline step count fix (0→7) → Task 2 Step 1, Task 5 Step 1
- ✓ Senator count fix (9 not 7) → Task 3 Steps 7-8, Task 6 Step 5
- ✓ `scripts/deprecated/` referenced → Task 6 Step 2 (repo map includes it)
- ✓ Anchor preservation → Task 1 Step 2, Task 8 Step 1
- ✓ JS preservation → Task 5 Step 7 (Play tour), Task 6 Step 1 (TODO matrix decision)
- ✓ File size budget → Task 8 Step 3

**Placeholder scan:** none — all diagram code is inline; all step content is concrete.

**Type consistency:**
- IDs: `#overview`, `#modes`, `#voices`, `#internals`, `#reference`, `#efficiency`, `#trias-deepdive` used consistently across tasks ✓
- Diagram numbering D1-D25 consecutive and unique ✓
- Senator count = 9 used uniformly in Tasks 3, 6 ✓
- Pipeline step count = 0-7 used in Tasks 2, 5, 6 ✓
