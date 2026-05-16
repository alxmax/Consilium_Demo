# Architecture HTML Update — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge `consilium-viz.html` into `docs/architecture.html` (3 new tabs + Mermaid), redesign `docs/senate/architecture.html` to match the main file's design system, delete `consilium-viz.html`.

**Architecture:** Additive edits to `docs/architecture.html` (add Mermaid CDN, 2 new tabs: Dialectic Flow + TODO Matrix; enrich Memory tab with Observe→Think→Act→Learn diagram; add Mermaid flowchart in Flow tab). Complete rewrite of `docs/senate/architecture.html` (same CSS system, tab-based navigation, Mermaid for Overview/Dispatch/Verdict). Deletion of `consilium-viz.html`.

**Tech Stack:** HTML + CSS + Mermaid.js v10 (CDN, no build step) + vanilla JS (SVG bubble chart for TODO Matrix)

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `docs/architecture.html` | Modify | Add Mermaid CDN + CSS; 2 new nav buttons; Mermaid overview in Flow tab; O→T→A→L in Memory tab; 2 new tab sections (Dialectic + TODO Matrix) |
| `docs/senate/architecture.html` | Complete rewrite | New tab-based layout, gold dark theme, Mermaid for layers/dispatch/verdict |
| `consilium-viz.html` | Delete | Content fully merged into main |

---

## Task 1: Add Mermaid.js infrastructure to docs/architecture.html

**Files:**
- Modify: `docs/architecture.html` (3 targeted edits)

- [ ] **Step 1: Add Mermaid CDN script in `<head>`**

Find this line (around line 5):
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Insert immediately after it:
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
```

- [ ] **Step 2: Add `.mermaid` CSS**

Find in the CSS block (before `</style>`, around line 1062):
```css
  @media (max-width: 900px) {
    .voices, .schemes, .modes, .flow, .rail-grid { grid-template-columns: 1fr; }
```

Insert before that block:
```css
  /* ============== MERMAID ============== */
  .mermaid { text-align: center; margin: 0 auto; }
  .mermaid svg { max-width: 100%; height: auto; }
  .mermaid-wrap { background: var(--inset); border: 1px solid var(--line);
    border-radius: 10px; padding: 20px; margin-bottom: 24px; }
  .mermaid-wrap h3 { margin: 0 0 16px; font-size: 13px; font-weight: 600;
    color: var(--muted); text-transform: uppercase; letter-spacing: .8px; }

```

- [ ] **Step 3: Add `mermaid.initialize()` call**

Find in the `<script>` block (around line 3838):
```javascript
  (function() {
    var tabs = document.querySelectorAll('nav.tabs button');
```

Insert before that line:
```javascript
  mermaid.initialize({ startOnLoad: true, securityLevel: 'loose',
    theme: 'dark',
    themeVariables: {
      primaryColor: '#21262d', primaryTextColor: '#e5e7eb',
      primaryBorderColor: '#2d3441', lineColor: '#9ca3af',
      secondaryColor: '#11151c', tertiaryColor: '#0f1419',
      edgeLabelBackground: '#11151c'
    }
  });

```

- [ ] **Step 4: Open `docs/architecture.html` in browser and verify**

No console errors. All existing tabs (Architecture, Flow, Modes, Memory, Patterns, Voices, Files, Git) still render. Mermaid script loads.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): add Mermaid.js infrastructure to architecture.html"
```

---

## Task 2: Add Mermaid overview to Flow tab

**Files:**
- Modify: `docs/architecture.html` (1 insertion in Flow tab, around line 1335)

- [ ] **Step 1: Insert Mermaid flowchart before step-cards**

Find in the Flow section:
```html
  <section class="tab" id="flow">

    <h2>Pașii 0 → 6 (cu aux 1.5, 5b, 5c, 5d)</h2>
    <div class="flow">
```

Replace with:
```html
  <section class="tab" id="flow">

    <h2>Pașii 0 → 6 (cu aux 1.5, 5b, 5c, 5d)</h2>

    <div class="mermaid-wrap" style="max-width:900px;margin-bottom:32px">
      <h3>Overview — pipeline complet</h3>
      <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart LR
    S0["Step 0\nBootstrap\npriors.py"]:::aux
    S1["Step 1\nGoal\nsuccess_criterion"]:::step
    S15["1.5\nScope Gate\nscope_gate.py"]:::aux
    S2["Step 2\nGenerator\ncandidates[]"]:::gen
    S3["Step 3\nControl\nverdicts[]"]:::ctl
    S4["Step 4\nConservator\nrisk_scores[]"]:::con
    S5["Step 5\nAggregator"]:::agg
    S5b["5b\nConfidence\nconfidence.py"]:::aux
    S5c["5c\nMeta-critic\noptional"]:::aux
    S6["Step 6\nOutput\nruns/*.json"]:::out

    S0 --> S1 --> S15 --> S2 --> S3 --> S4 --> S5 --> S5b --> S5c --> S6
    S6 -.->|"priors loop"| S0

    classDef aux  fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef step fill:#11151c,stroke:#2d3441,color:#e5e7eb
    classDef gen  fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef ctl  fill:#182338,stroke:#2a3f5f,color:#93c5fd
    classDef con  fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
    classDef agg  fill:#0a2e23,stroke:#145c45,color:#6ee7b7
    classDef out  fill:#221830,stroke:#4c2a6b,color:#d8b4fe
      </div>
    </div>

    <div class="flow">
```

- [ ] **Step 2: Verify in browser**

Open Flow tab. Mermaid diagram renders above the HTML step-cards. Existing step-cards still visible below.

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): add Mermaid pipeline overview to Flow tab"
```

---

## Task 3: Add Observe→Think→Act→Learn diagram to Memory tab

**Files:**
- Modify: `docs/architecture.html` (append to Memory section before its closing `</section>`)

- [ ] **Step 1: Find the closing tag of the Memory section**

The Memory section (`id="memory"`) ends just before `<section class="tab" id="patterns">` (around line 3101). Find the last block in the Memory section — it's a `</section>` tag.

Find:
```html
  </section>

  <!-- ============== TAB 5 ============== -->
  <section class="tab" id="patterns">
```

Insert before that block:
```html
    <h2>Observe → Think → Act → Learn</h2>
    <p style="color:var(--muted);font-size:13px;margin:-8px 0 20px">Cum funcționează consilium ca agent loop. Memory tiers se leagă de fiecare fază.</p>

    <div class="mermaid-wrap" style="max-width:1000px">
      <h3>Agent loop + memory tiers</h3>
      <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart LR
    OBS["OBSERVE\nStep 1: gather context\nscope_gate.py"]:::obs
    THINK["THINK\nStep 2: Generator\nStep 3: Control\nStep 4: Conservator"]:::think
    ACT["ACT\nStep 5: aggregator.py\nchosen_approach"]:::act
    LEARN["LEARN\nStep 6: log_feedback.py\nFEEDBACK.html"]:::learn

    SHORT["Short-term\ncontext window\ndeliberarea curentă"]:::mem
    MED["Medium-term\nruns/*.json\nepisodic — fiecare run"]:::mem
    LONG["Long-term\nFEEDBACK.html\npriors.py soft weights"]:::mem

    OBS --> THINK --> ACT --> LEARN
    LEARN -.->|"priors loop\nStep 0"| OBS

    ACT --- SHORT
    LEARN --- MED
    OBS --- LONG

    classDef obs   fill:#2a2410,stroke:#fbbf24,color:#fbbf24
    classDef think fill:#182338,stroke:#60a5fa,color:#93c5fd
    classDef act   fill:#0a2e23,stroke:#34d399,color:#6ee7b7
    classDef learn fill:#221830,stroke:#c084fc,color:#d8b4fe
    classDef mem   fill:#11151c,stroke:#2d3441,color:#9ca3af
      </div>
    </div>

```

- [ ] **Step 2: Verify in browser**

Open Memory tab. New Mermaid diagram appears below existing 3-tier content. Existing content intact.

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): add Observe-Think-Act-Learn Mermaid to Memory tab"
```

---

## Task 4: Add Dialectic Flow tab to docs/architecture.html

**Files:**
- Modify: `docs/architecture.html` (nav button + new section before `</main>`)

- [ ] **Step 1: Add nav button**

Find:
```html
  <button data-tab="git"><span>Git</span><span class="tab-sub">workflow + self-improvement loop</span></button>
```

Replace with:
```html
  <button data-tab="git"><span>Git</span><span class="tab-sub">workflow + self-improvement loop</span></button>
  <button data-tab="dialectic"><span>Dialectic</span><span class="tab-sub">Pass 1 + Pass 2 cross-review</span></button>
```

- [ ] **Step 2: Add Dialectic tab section**

Find (after the Git section closes, before `</main>`):
```html
</main>
```

Insert before `</main>`:
```html

  <!-- ============== TAB: DIALECTIC ============== -->
  <section class="tab" id="dialectic">

    <h2>Dialectic Mode — flow complet</h2>
    <p style="color:var(--muted);font-size:13.5px;margin:-8px 0 24px">Pass 1: izolat (parallel). Pass 2: fiecare voce vede output-urile celorlalte și revizuiește sau menține.</p>

    <div class="mermaid-wrap" style="max-width:900px;margin-bottom:32px">
      <h3>Sequence — Pass 1 + Pass 2</h3>
      <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
sequenceDiagram
    autonumber
    participant G as Generator
    participant C as Control
    participant K as Conservator
    participant M as dialectic_merge.py
    participant A as aggregator.py

    Note over G,K: PASS 1 — izolat (parallel subagents)
    G->>M: candidates[] + adversarial_* + do_nothing
    C->>M: verdicts[] (valid: true/false, issues, tests_to_write)
    K->>M: scores[] (risk_score, factors, rollback_recipe)

    Note over G,K: PASS 2 — cross-review (fiecare vede Pass 1 al celorlalți)
    M-->>G: Control verdicts + Conservator scores
    M-->>C: Generator candidates + Conservator scores
    M-->>K: Generator candidates + Control verdicts

    G->>M: revision{what_changed, peer_evidence} / maintained{peer_claim, dissent}
    C->>M: revision / maintained (NU revizuiește pentru risc — doar corectitudine)
    K->>M: revision / maintained (aplică -0.15 regression dacă Control adaugă tests)

    Note over M: Merge + revision_log + convergence check
    M->>A: merged candidates[] + revision_log
    A->>A: conservative_override voting + veto @ risk > 0.8
    A-->>G: chosen_approach + confidence + alternatives[why_not]
      </div>
    </div>

    <div class="mermaid-wrap" style="max-width:900px">
      <h3>Reguli per-voce în Pass 2</h3>
      <div class="mermaid">
%%{init: {'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart LR
    subgraph P2G ["Generator Pass 2"]
      direction TB
      GA["pentru fiecare candidat:\nrevision SAU maintained\nNiciodată ambele, niciodată niciunul"]
      GB["NU retrage candidați\npe baza scorului Conservator"]
    end

    subgraph P2C ["Control Pass 2"]
      direction TB
      CA["revizuiește doar pt\ncorectitudine, NU risc"]
      CB["dacă sketch schimbat\nsubstanțial → re-validare completă"]
    end

    subgraph P2K ["Conservator Pass 2"]
      direction TB
      KA["aplică -0.15 regression_risk\ndacă Control adaugă tests_to_write"]
      KB["handling Control flip\nfalse→true: scorează\ntrue→false: retrage"]
    end

    P2G --> MERGE["dialectic_merge.py\nrevision_log\nconvergence check"]
    P2C --> MERGE
    P2K --> MERGE

    style P2G  fill:#2a2410,stroke:#fbbf24,color:#fbbf24
    style P2C  fill:#182338,stroke:#60a5fa,color:#93c5fd
    style P2K  fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
    style MERGE fill:#0a2e23,stroke:#145c45,color:#6ee7b7
      </div>
    </div>

  </section>

```

- [ ] **Step 3: Verify in browser**

Click "Dialectic" tab. Both Mermaid diagrams render. Sequence diagram shows Pass 1 + Pass 2. Flowchart shows per-voice rules.

- [ ] **Step 4: Commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): add Dialectic Flow tab with Mermaid sequence + flowchart"
```

---

## Task 5: Add TODO Matrix tab to docs/architecture.html

**Files:**
- Modify: `docs/architecture.html` (nav button + new section + CSS + JS)

The TODO Matrix uses a custom SVG bubble chart (Mermaid does not support scatter plots). Copy the existing implementation from `consilium-viz.html`.

- [ ] **Step 1: Add CSS for TODO Matrix**

Find in CSS (before `</style>`):
```css
  /* ============== MERMAID ============== */
```

Insert before it:
```css
  /* ============== TODO MATRIX ============== */
  .todo-matrix-container { position: relative; background: var(--card-bg);
    border: 1px solid var(--line); border-radius: 10px; padding: 32px;
    max-width: 900px; margin: 0 auto; }
  .todo-matrix-container h3 { margin: 0 0 4px; font-size: 13px; font-weight: 600;
    color: var(--muted); text-transform: uppercase; letter-spacing: .8px; }
  .todo-matrix-svg { width: 100%; height: 520px; }
  .todo-legend { display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
  .todo-legend-item { display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: var(--muted); }
  .todo-legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  #todoTooltip { position: fixed; background: var(--card-bg); border: 1px solid var(--line);
    border-radius: 6px; padding: 10px 14px; font-size: 12px; max-width: 280px;
    pointer-events: none; z-index: 999; display: none; line-height: 1.5; }
  #todoTooltip .tip-title { font-weight: 600; color: var(--ink); margin-bottom: 4px; }
  #todoTooltip .tip-body  { color: var(--muted); }

```

- [ ] **Step 2: Add nav button**

Find:
```html
  <button data-tab="dialectic"><span>Dialectic</span><span class="tab-sub">Pass 1 + Pass 2 cross-review</span></button>
```

Replace with:
```html
  <button data-tab="dialectic"><span>Dialectic</span><span class="tab-sub">Pass 1 + Pass 2 cross-review</span></button>
  <button data-tab="todo-matrix"><span>TODO Matrix</span><span class="tab-sub">26 iteme · impact × efort</span></button>
```

- [ ] **Step 3: Add TODO Matrix tab section**

Find:
```html
  <!-- ============== TAB: DIALECTIC ============== -->
```

Insert before it:
```html
  <!-- ============== TAB: TODO MATRIX ============== -->
  <section class="tab" id="todo-matrix">

    <div class="todo-matrix-container">
      <h3>TO_DO Priority Matrix</h3>
      <p style="font-size:12px;color:var(--muted);margin-bottom:24px">Hover pe fiecare item pentru detalii — impact (sus) × efort (dreapta)</p>
      <svg class="todo-matrix-svg" id="todoMatrixSvg" viewBox="0 0 820 500"></svg>
      <div class="todo-legend">
        <div class="todo-legend-item"><div class="todo-legend-dot" style="background:#fbbf24"></div> Prompt (Pass 1)</div>
        <div class="todo-legend-item"><div class="todo-legend-dot" style="background:#f97316"></div> Prompt (Pass 2 dialectic)</div>
        <div class="todo-legend-item"><div class="todo-legend-dot" style="background:#60a5fa"></div> Skill / Script</div>
        <div class="todo-legend-item"><div class="todo-legend-dot" style="background:#f87171"></div> Arhitectură</div>
      </div>
    </div>

  </section>

```

- [ ] **Step 4: Add TODO Matrix JS**

Find in `<script>`:
```javascript
  mermaid.initialize({
```

Insert before it:
```javascript
  // ── TODO MATRIX ───────────────────────────────────────────────────────
  var todoItems = [
    [1,  "#1 success_criterion Input",         3, 0, "prompt1",  "Adaugă success_criterion explicit în Input la toate 3 voci. Impact maxim, 1 linie per fișier."],
    [2,  "#2 Conservator: risc ≠ valoare",     3, 0, "prompt1",  "Conservator nu trebuie să influențeze outcome prin inflate de scoruri. Mindset fix."],
    [3,  "#3 Control: standard consistent",    3, 0, "prompt1",  "Aplică același standard tuturor candidaților. Familiarity ≠ validity."],
    [4,  "#4 Generator: nu ancora",            2, 0, "prompt1",  "Generează soluția obvioasă ultima. Think at multiple levels."],
    [5,  "#5 ID preservation",                 2, 0, "prompt1",  "id trebuie păstrat verbatim Generator → Control → Conservator."],
    [6,  "#6 Shared/core code def.",           2, 0, "prompt1",  "Conservator nu are definiție pentru 'shared/core'. Adaugă lista din Generator."],
    [7,  "#7 Sketch depth",                    2, 0, "prompt1",  "2-5 propoziții sau pseudocod. Nu 'change X to Y'."],
    [8,  "#8 Control: citește fișiere",        2, 0, "prompt1",  "Dacă nu poți verifica fără fișier, citește-l. Nu specula și marchezi verified."],
    [9,  "#9 Goal-fit → pasul 0",              2, 1, "prompt1",  "Mută goal-fit check înainte de types/logic în Control. Fail fast."],
    [10, "#10 Cap regression_risk stack",      2, 0, "prompt1",  "Max -0.20 cumulativ indiferent de câte mitigări. Documentează fiecare."],
    [11, "#11 Ireversibil by nature",          2, 1, "prompt1",  "Published API → mitigation_steps + irreversible:true în loc de rollback_recipe fake."],
    [12, "#12 probe_change în Cons. Input",    2, 0, "prompt1",  "Menționează că Conservator poate primi files_changed, lines_changed, churn."],
    [13, "#13 Single retry confidence",        2, 1, "skill",    "Un singur retry cu context îmbogățit pt top 2 candidați când confidence < 0.7."],
    [14, "#14 Meta-critic deliberare",         3, 2, "arch",     "Detectează: divergență falsă Generator, speculație Control, 0.5-shrug Conservator."],
    [15, "#15 Feedback din producție",         3, 2, "arch",     "CLI consilium mark-outcome <run> BAD. Feedback real, nu subiectiv imediat."],
    [16, "#16 Meta-controller",               2, 2, "arch",     "Componentă care poate decide restart / enrich-context / skip-voice mid-deliberation."],
    [17, "#17 Semantic memory",               2, 3, "arch",     "Index embeddings pe runs/*.json. Query 'deliberări similare cu această schimbare'."],
    [18, "#18 Observe→Think→Act formal",      2, 3, "arch",     "State machine explicită. Permite restart, enrichment, skip condiționat."],
    [19, "#19 Memory tiers formalizate",      1, 2, "arch",     "API uniform short/medium/long. Valoros doar dacă semantic memory e implementată."],
    [20, "#20 Mechanism variation ex.",       1, 0, "prompt1",  "Exemplu concret pt 'mechanism' axis în Generator Constraints."],
    [21, "#21 Gen Pass2: nu retrage pt risc", 3, 0, "prompt2",  "Generator nu trebuie să atenueze candidați în Pass 2 pe baza scorului Conservator."],
    [22, "#22 Ctrl Pass2: re-validare sketch",3, 0, "prompt2",  "Dacă Generator schimbă sketch substanțial → re-validare completă în Control Pass 2."],
    [23, "#23 Cons Pass2: Control flip",      2, 0, "prompt2",  "Conservator nu știe ce face când Control flips valid: false→true sau invers."],
    [24, "#24 Candidați noi în Pass 2",       2, 1, "prompt2",  "Protocol explicit: interzis sau mini-pass suplimentar pentru Control + Conservator."],
    [25, "#25 Convergence check",             2, 0, "skill",    "Dacă toate vocile emit maintained → convergence:true + warning în revision_log."],
    [26, "#26 Dialectic vs parallel criteria",2, 0, "skill",    "Tabelă de decizie clară în SKILL.md: când folosești fiecare mod."]
  ];
  var todoCatColor = { prompt1:'#fbbf24', prompt2:'#f97316', skill:'#60a5fa', arch:'#f87171' };
  var todoDrawn = false;

  function drawTodoMatrix() {
    if (todoDrawn) return;
    todoDrawn = true;
    var svg = document.getElementById('todoMatrixSvg');
    if (!svg) return;
    var W = 820, H = 500;
    var PAD = { left: 60, right: 20, top: 20, bottom: 50 };
    var IW = W - PAD.left - PAD.right;
    var IH = H - PAD.top - PAD.bottom;
    var effortLabels = ['Mic', 'Mic-Med', 'Mare', 'Foarte Mare'];
    var impactLabels = ['Scăzut', 'Mediu', 'Înalt'];
    function xPos(e) { return PAD.left + (e / 3) * IW; }
    function yPos(i) { return PAD.top + IH - ((i - 1) / 2) * IH; }
    var html = '';
    for (var i = 0; i <= 3; i++) {
      var x = xPos(i);
      html += '<line x1="'+x+'" y1="'+PAD.top+'" x2="'+x+'" y2="'+(PAD.top+IH)+'" stroke="#2d3441" stroke-width="1"/>';
      html += '<text x="'+x+'" y="'+(H-10)+'" text-anchor="middle" fill="#9ca3af" font-size="11">'+effortLabels[i]+'</text>';
    }
    for (var j = 1; j <= 3; j++) {
      var y = yPos(j);
      html += '<line x1="'+PAD.left+'" y1="'+y+'" x2="'+(PAD.left+IW)+'" y2="'+y+'" stroke="#2d3441" stroke-width="1"/>';
      html += '<text x="'+(PAD.left-8)+'" y="'+(y+4)+'" text-anchor="end" fill="#9ca3af" font-size="11">'+impactLabels[j-1]+'</text>';
    }
    html += '<text x="'+(PAD.left+IW/2)+'" y="'+(H-2)+'" text-anchor="middle" fill="#9ca3af" font-size="12" font-weight="600">EFORT →</text>';
    html += '<text x="12" y="'+(PAD.top+IH/2)+'" text-anchor="middle" fill="#9ca3af" font-size="12" font-weight="600" transform="rotate(-90,12,'+(PAD.top+IH/2)+')">IMPACT →</text>';
    var placed = [];
    function jitter(bx, by, r) {
      var dx = 0, dy = 0;
      for (var k = 0; k < placed.length; k++) {
        var dist = Math.sqrt(Math.pow(bx+dx-placed[k].x,2)+Math.pow(by+dy-placed[k].y,2));
        if (dist < r*2.2) {
          var angle = Math.atan2(by+dy-placed[k].y, bx+dx-placed[k].x);
          dx += Math.cos(angle)*(r*2.2-dist)*0.5;
          dy += Math.sin(angle)*(r*2.2-dist)*0.5;
        }
      }
      placed.push({x:bx+dx, y:by+dy});
      return [bx+dx, by+dy];
    }
    for (var t = 0; t < todoItems.length; t++) {
      var item = todoItems[t];
      var id = item[0], label = item[1], impact = item[2], effort = item[3], cat = item[4], desc = item[5];
      var bx = xPos(effort), by = yPos(impact), r = 16;
      var pos = jitter(bx, by, r);
      var cx = pos[0], cy = pos[1];
      var col = todoCatColor[cat];
      var safeDesc = desc.replace(/"/g,'&quot;').replace(/'/g,'&#39;');
      var safeLabel = label.replace(/"/g,'&quot;');
      html += '<g class="todo-bubble" data-title="'+safeLabel+'" data-desc="'+safeDesc+'" style="cursor:pointer">';
      html += '<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" fill="'+col+'22" stroke="'+col+'" stroke-width="1.5" opacity="0.9"/>';
      html += '<text x="'+cx+'" y="'+(cy+4)+'" text-anchor="middle" fill="'+col+'" font-size="10" font-weight="700">'+id+'</text>';
      html += '</g>';
    }
    svg.innerHTML = html;
    var tip = document.getElementById('todoTooltip');
    if (!tip) return;
    var tipTitle = tip.querySelector('.tip-title');
    var tipBody  = tip.querySelector('.tip-body');
    svg.querySelectorAll('.todo-bubble').forEach(function(el) {
      el.addEventListener('mousemove', function(e) {
        tipTitle.textContent = el.dataset.title;
        tipBody.textContent  = el.dataset.desc;
        tip.style.display = 'block';
        tip.style.left = (e.clientX + 14) + 'px';
        tip.style.top  = (e.clientY - 10) + 'px';
      });
      el.addEventListener('mouseleave', function() { tip.style.display = 'none'; });
    });
  }

```

- [ ] **Step 5: Add tooltip div and wire up drawTodoMatrix on tab switch**

Find in `<body>` (just before `<script>`):
```html
<div class="pat-tour-progress" id="patTourProgress"><span></span></div>
```

Insert after it:
```html
<div id="todoTooltip"><div class="tip-title"></div><div class="tip-body"></div></div>
```

Then find the tab-switch handler in `<script>`:
```javascript
      btn.addEventListener('click', function() {
```

Read a few more lines until you find where the tab switch happens. Find the block that calls `syncPlayBtn` and add `drawTodoMatrix` when the todo-matrix tab is activated. Find:
```javascript
        function activate(target) {
```

If this function exists, find inside it the part that runs after switching and add:
```javascript
          if (target === 'todo-matrix') drawTodoMatrix();
```

If no `activate` function exists, find instead the click handler that does `data-tab` switching and add the call there. Look for:
```javascript
        sections.forEach(function(s) { s.classList.remove('active'); });
```

After that block, add:
```javascript
        if (target === 'todo-matrix') drawTodoMatrix();
```

- [ ] **Step 6: Verify in browser**

Click "TODO Matrix" tab. Bubble chart renders with 26 colored dots. Hovering shows tooltip with TODO description. Check categories: yellow = prompt1, orange = prompt2, blue = skill, red = arch.

- [ ] **Step 7: Commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): add TODO Matrix tab with interactive bubble chart"
```

---

## Task 6: Redesign docs/senate/architecture.html

**Files:**
- Rewrite: `docs/senate/architecture.html` (complete replacement)

This is a full rewrite. All content from the current file is preserved — only structure and styling change.

- [ ] **Step 1: Read current file for content reference**

Before writing, confirm the senators list (§2) is: Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon.

- [ ] **Step 2: Write new docs/senate/architecture.html**

Replace the entire file with:

```html
<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Senate — Architecture</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  :root {
    --bg: #0f1419; --ink: #e5e7eb; --muted: #9ca3af; --line: #2d3441;
    --card-bg: #181d27; --inset: #11151c;
    --gold: #fbbf24; --gold-soft: #2a2410; --gold-border: #5c4a14;
    --gen: #fbbf24; --gen-soft: #2a2410; --gen-border: #5c4a14; --gen-text: #fbbf24;
    --ctl: #60a5fa; --ctl-soft: #182338; --ctl-border: #2a3f5f; --ctl-text: #93c5fd;
    --con: #f87171; --con-soft: #2a1818; --con-border: #5c2a2a; --con-text: #fca5a5;
    --accent: #34d399; --accent-soft: #0a2e23; --accent-border: #145c45; --accent-text: #6ee7b7;
    --trias: #c084fc; --trias-soft: #221830; --trias-border: #4c2a6b; --trias-text: #d8b4fe;
    --amber: #f59e0b; --purple: #c084fc; --green: #34d399; --red: #f87171;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; color: var(--ink);
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  body {
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse 80% 60% at 15% 0%, rgba(217,168,116,.18) 0%, transparent 55%),
      radial-gradient(ellipse 70% 50% at 85% 0%, rgba(192,154,110,.14) 0%, transparent 55%),
      radial-gradient(circle, rgba(255,255,255,.022) 1px, transparent 1px);
    background-size: auto, auto, 28px 28px;
    background-attachment: fixed, fixed, fixed;
  }
  header { padding: 28px 40px 0; }
  header h1 { margin: 0 0 4px; font-size: 22px; letter-spacing: -.01em; }
  header .sub { color: var(--muted); font-size: 13px; }
  nav.tabs { display: flex; gap: 4px; padding: 22px 40px 0; border-bottom: 1px solid var(--line);
    position: sticky; top: 0; background: var(--bg); z-index: 10; flex-wrap: wrap; }
  nav.tabs button { appearance: none; background: transparent; border: 0; padding: 10px 18px;
    font: inherit; font-weight: 500; color: var(--muted); cursor: pointer;
    border-bottom: 2px solid transparent; margin-bottom: -1px; }
  nav.tabs button:hover { color: var(--ink); }
  nav.tabs button.active { color: var(--ink); border-bottom-color: var(--gold); }
  main { padding: 32px 40px 80px; max-width: 1240px; margin: 0 auto; }
  section.tab { display: none; }
  section.tab.active { display: block; }
  h2 { margin: 0 0 18px; font-size: 16px; letter-spacing: .04em;
    text-transform: uppercase; color: var(--muted); }
  h3 { margin: 28px 0 12px; font-size: 15px; }
  p { margin: 0 0 14px; font-size: 13.5px; line-height: 1.6; }
  code { font-family: ui-monospace,"SF Mono",Menlo,Consolas,monospace;
    font-size: 12.5px; background: var(--inset); padding: 1px 5px; border-radius: 3px; }
  a { color: var(--ctl-text); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .note { color: var(--muted); font-size: 13px; margin-top: 16px; }

  /* Mermaid */
  .mermaid { text-align: center; }
  .mermaid svg { max-width: 100%; height: auto; }
  .mermaid-wrap { background: var(--inset); border: 1px solid var(--line);
    border-radius: 10px; padding: 20px; margin-bottom: 24px; }
  .mermaid-wrap h3 { margin: 0 0 16px; font-size: 13px; font-weight: 600;
    color: var(--muted); text-transform: uppercase; letter-spacing: .8px; }

  /* Senator cards */
  .senator-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr));
    gap: 14px; margin: 20px 0; }
  .senator-card { background: var(--card-bg); border: 1px solid var(--line);
    border-left: 3px solid var(--gold); border-radius: 8px; padding: 14px 16px; }
  .senator-card.w { border-left-color: #ec4899; }
  .senator-card.a { border-left-color: var(--ctl); }
  .senator-card.c { border-left-color: var(--accent); }
  .senator-card.s { border-left-color: var(--trias); }
  .senator-card.m { border-left-color: var(--gold); }
  .senator-card.d { border-left-color: var(--con); }
  .senator-card.n { border-left-color: var(--amber); }
  .senator-card .name { font-size: 17px; font-weight: 700; margin-bottom: 2px; }
  .senator-card .spec { font-size: 11px; color: var(--muted); text-transform: uppercase;
    letter-spacing: .06em; margin-bottom: 10px; }
  .senator-card .question { font-size: 13px; font-style: italic; color: var(--ink);
    padding-left: 10px; border-left: 2px solid var(--line); margin: 8px 0; }
  .senator-card .field { font-family: ui-monospace,monospace; font-size: 11px;
    color: var(--gold); margin-top: 6px; }

  /* Verdict cards */
  .verdict-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 14px; margin: 20px 0; }
  .verdict-card { background: var(--card-bg); border: 1px solid var(--line);
    border-radius: 8px; padding: 16px; }
  .verdict-card .label { font-size: 11px; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; margin-bottom: 6px; }
  .verdict-card .rule { font-family: ui-monospace,monospace; font-size: 13px;
    color: var(--muted); margin-bottom: 8px; }
  .verdict-card .action { font-size: 13px; }
  .verdict-card.go  { background: var(--accent-soft); border-color: var(--accent-border); }
  .verdict-card.go .label { color: var(--accent-text); }
  .verdict-card.stop { background: var(--con-soft); border-color: var(--con-border); }
  .verdict-card.stop .label { color: var(--con-text); }
  .verdict-card.mod  { background: var(--gold-soft); border-color: var(--gold-border); }
  .verdict-card.mod .label { color: var(--gold); }
  .verdict-card.unr { background: var(--inset); border-color: var(--line); opacity: .8; }
  .verdict-card.unr .label { color: var(--muted); }

  /* File tree */
  .file-tree { background: var(--card-bg); border: 1px solid var(--line);
    border-radius: 8px; padding: 18px 24px; font-family: ui-monospace,monospace;
    font-size: 12.5px; line-height: 1.6; }
  .file-tree .new { color: var(--accent-text); }
  .file-tree .note { color: var(--muted); font-style: italic; }

  /* Tables */
  table.data { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
  table.data th, table.data td { text-align: left; padding: 10px 14px;
    border-bottom: 1px solid var(--line); }
  table.data th { background: var(--inset); font-weight: 600; color: var(--muted);
    font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
  table.data td { color: var(--ink); vertical-align: top; }
  table.data tr:hover td { background: var(--inset); }

  /* Code block */
  pre.code-block { background: var(--inset); border: 1px solid var(--line);
    border-radius: 6px; padding: 14px 16px; overflow-x: auto;
    font-family: ui-monospace,monospace; font-size: 12px;
    color: var(--muted); line-height: 1.5; margin: 12px 0; }

  /* Info card */
  .info-card { background: var(--gold-soft); border: 1px solid var(--gold-border);
    border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; font-size: 13px; }
  .info-card b { color: var(--gold); }

  /* Footer */
  footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--line);
    color: var(--muted); font-size: 12px; }

  @media (max-width: 900px) {
    main { padding: 24px 16px 60px; }
    nav.tabs { padding: 16px 16px 0; }
    header { padding: 20px 16px 0; }
    .senator-grid, .verdict-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header>
  <h1>Senate</h1>
  <div class="sub">Layer de governance pentru modificări la skill-ul consilium însuși</div>
</header>

<nav class="tabs" role="tablist">
  <button class="active" data-tab="overview">Overview</button>
  <button data-tab="senators">Senatori</button>
  <button data-tab="dispatch">Dispatch</button>
  <button data-tab="verdict">Verdict</button>
  <button data-tab="files">Fișiere &amp; Mod</button>
  <button data-tab="self-improvement">Self-improvement</button>
  <button data-tab="limits">Limitări &amp; Test</button>
</nav>

<main>

  <!-- ══════ TAB: OVERVIEW ══════ -->
  <section class="tab active" id="overview">

    <h2>§1 — Unde stă Senatul în consilium</h2>
    <p>3 layere distincte. Senatul e layer-ul de <strong>governance</strong> — nu intervine pe întrebări regulate, ci doar când skill-ul însuși urmează să fie modificat.</p>

    <div class="mermaid-wrap">
      <h3>Arhitectura pe layere</h3>
      <div class="mermaid">
%%{init:{'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c','clusterBkg':'#181d27'}}}%%
flowchart TD
    subgraph L3 ["L3 · Senate — governance (on-demand)"]
      direction LR
      S7["7 senatori\nparalel\nmodel: sonnet"]:::gov
      SYNTH["senate_synth.py\nquorum 5/7"]:::gov
      VV["Verdict\nGO / MODIFY / STOP\nUNREACHABLE"]:::gov
      S7 --> SYNTH --> VV
    end
    subgraph L2 ["L2 · Aggregation — per deliberare"]
      direction LR
      AGG["aggregator.py"]:::agg
      CONF["confidence.py"]:::agg
      REP["validate_report.py"]:::agg
      AGG --> CONF --> REP
    end
    subgraph L1 ["L1 · Deliberation — per întrebare"]
      direction LR
      GEN["Generator"]:::gen
      CTL["Control"]:::ctl
      CON["Conservator"]:::con
      GEN & CTL & CON --> AGG
    end
    VV -.->|"advisory only\nuser decide"| L1

    classDef gov fill:#221830,stroke:#c084fc,color:#d8b4fe
    classDef agg fill:#0a2e23,stroke:#145c45,color:#6ee7b7
    classDef gen fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef ctl fill:#182338,stroke:#2a3f5f,color:#93c5fd
    classDef con fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
      </div>
    </div>

    <div class="info-card">
      <b>Reguli de izolare:</b> L3 nu se invocă pe întrebări user; L1+L2 nu se invocă pe modificări la skill. Senatul e <b>advisory</b> — user-ul ia decizia finală.
    </div>

    <p>Citește înainte: secțiunea <em>„Senate mode (<code>senate</code>)"</em> din <a href="../../SKILL.md">SKILL.md</a>. Acest doc e schemele; SKILL.md e contractul.</p>

  </section>

  <!-- ══════ TAB: SENATORS ══════ -->
  <section class="tab" id="senators">

    <h2>§2 — Cei 7 senatori și lensele lor</h2>
    <p>Fiecare e o <strong>perspectivă cognitivă distinctă</strong>. Scope-ul declarat în <code>## Limite</code> din fiecare prompt; NU se suprapun.</p>

    <div class="senator-grid">
      <div class="senator-card w">
        <div class="name">Wittgenstein</div>
        <div class="spec">operational semantics</div>
        <div class="question">„E definit operațional? Cum verifici că s-a respectat?"</div>
        <div class="field">→ vague_terms_found[]</div>
      </div>
      <div class="senator-card a">
        <div class="name">Aurelius</div>
        <div class="spec">reversibility × magnitude</div>
        <div class="question">„E proporțional cu stake-ul? Reversibil?"</div>
        <div class="field">→ reversibility · magnitude · quadrant</div>
      </div>
      <div class="senator-card c">
        <div class="name">Confucius</div>
        <div class="spec">hierarchy &amp; precedent</div>
        <div class="question">„Cine are autoritate aici? Avem precedente?"</div>
        <div class="field">→ hierarchy_check · precedent_search[]</div>
      </div>
      <div class="senator-card s">
        <div class="name">Socrate</div>
        <div class="spec">hidden assumptions</div>
        <div class="question">„Ce presupui fără să declari? Dacă-i falsă?"</div>
        <div class="field">→ hidden_assumptions[].load_bearing</div>
      </div>
      <div class="senator-card m">
        <div class="name">Musk</div>
        <div class="spec">aggressive deletion</div>
        <div class="question">„Ce poți șterge fără să pierzi funcția?"</div>
        <div class="field">→ components_attacked[].vote</div>
      </div>
      <div class="senator-card d">
        <div class="name">Dimon</div>
        <div class="spec">stress test &amp; counterparty</div>
        <div class="question">„Ce dacă eșuează? Cine plătește?"</div>
        <div class="field">→ stress_scenarios[].failure_mode</div>
      </div>
      <div class="senator-card n">
        <div class="name">Napoleon</div>
        <div class="spec">cost &amp; terrain</div>
        <div class="question">„Câți tokens? În ce stare e operatorul?"</div>
        <div class="field">→ cost_estimate · terrain_check</div>
      </div>
    </div>

    <p class="note">Toți emit <code>vote</code> (GO/MODIFY/STOP) și <code>modify_request</code>. Ortogonalitatea e validată prin secțiunea <code>## Limite</code> din fiecare prompt.</p>

  </section>

  <!-- ══════ TAB: DISPATCH ══════ -->
  <section class="tab" id="dispatch">

    <h2>§3 — Flow de dispatch</h2>
    <p>Orchestrator-ul (Claude când execută <code>/consilium senate</code>) urmează acest flow. Senatul nu se invocă automat.</p>

    <div class="mermaid-wrap">
      <h3>Sequence — orchestrator → 7 senatori → sinteză</h3>
      <div class="mermaid">
%%{init:{'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant W as Wittgenstein
    participant Au as Aurelius
    participant Co as Confucius
    participant So as Socrate
    participant M as Musk
    participant D as Dimon
    participant N as Napoleon
    participant Sy as senate_synth.py

    U->>O: propunere (ce, de ce, fișiere, criterion)
    Note over O: /consilium senate
    O->>W: prompt senator + input (model: sonnet)
    O->>Au: prompt senator + input (model: sonnet)
    O->>Co: prompt senator + input (model: sonnet)
    O->>So: prompt senator + input (model: sonnet)
    O->>M: prompt senator + input (model: sonnet)
    O->>D: prompt senator + input (model: sonnet)
    O->>N: prompt senator + input (model: sonnet)
    Note over W,N: paralel — nu văd unii pe alții
    W-->>O: {vote, modify_request, ...}
    Au-->>O: {vote, modify_request, ...}
    Co-->>O: {vote, modify_request, ...}
    So-->>O: {vote, modify_request, ...}
    M-->>O: {vote, modify_request, ...}
    D-->>O: {vote, modify_request, ...}
    N-->>O: {vote, modify_request, ...}
    O->>Sy: 7 JSON-uri
    Note over Sy: tally + compute_verdict + collect_modify_requests
    Sy-->>O: verdict + modify_requests[] + warnings[]
    O-->>U: verdict + recomandări (user decide)
      </div>
    </div>

    <p class="note">Retry 1× pe senator absent / JSON malformat. La eșec persistent → marchează <code>absent</code> și continuă. Dacă <code>voters_present &lt; 5</code> → verdict <code>UNREACHABLE</code>.</p>

  </section>

  <!-- ══════ TAB: VERDICT ══════ -->
  <section class="tab" id="verdict">

    <h2>§4 — Logica verdictului</h2>
    <p>Quorum 5/7. Cazul <code>UNREACHABLE</code> surfacează când restul de senatori nu pot atinge matematic quorum-ul.</p>

    <div class="verdict-grid">
      <div class="verdict-card go">
        <div class="label">verdict GO</div>
        <div class="rule">GO ≥ 5/7</div>
        <div class="action">Procedezi cu implementarea.</div>
      </div>
      <div class="verdict-card stop">
        <div class="label">verdict STOP</div>
        <div class="rule">STOP ≥ 5/7</div>
        <div class="action">Revizuie propunerea sau override explicit.</div>
      </div>
      <div class="verdict-card mod">
        <div class="label">verdict MODIFY</div>
        <div class="rule">orice altă combinație (default)</div>
        <div class="action">Aplică modify_requests și (opțional) re-rulează.</div>
      </div>
      <div class="verdict-card unr">
        <div class="label">verdict UNREACHABLE</div>
        <div class="rule">voters_present &lt; 5</div>
        <div class="action">Verdict structurally biased. Orchestrator escaladează la user.</div>
      </div>
    </div>

    <div class="mermaid-wrap">
      <h3>Arborele de decizie</h3>
      <div class="mermaid">
%%{init:{'theme':'dark','themeVariables':{'primaryColor':'#21262d','primaryTextColor':'#e5e7eb','primaryBorderColor':'#2d3441','lineColor':'#9ca3af','edgeLabelBackground':'#11151c'}}}%%
flowchart TD
    IN["7 voturi colectate\n(minus absenți/malformat)"]
    VP{"voters_present ≥ 5?"}
    RUNREACH["UNREACHABLE\n+ warning structural"]:::unr
    COUNT["Numără GO și STOP"]
    GO{"GO ≥ 5/7?"}
    STOP{"STOP ≥ 5/7?"}
    RGO["GO\nProcedezi"]:::go
    RSTOP["STOP\nRevizuie"]:::stop
    RMOD["MODIFY (default)\nAplică modify_requests"]:::mod

    IN --> VP
    VP -->|da| COUNT
    VP -->|nu| RUNREACH
    COUNT --> GO
    GO -->|da| RGO
    GO -->|nu| STOP
    STOP -->|da| RSTOP
    STOP -->|nu| RMOD

    classDef go   fill:#0a2e23,stroke:#145c45,color:#6ee7b7
    classDef stop fill:#2a1818,stroke:#5c2a2a,color:#fca5a5
    classDef mod  fill:#2a2410,stroke:#5c4a14,color:#fbbf24
    classDef unr  fill:#11151c,stroke:#2d3441,color:#9ca3af
      </div>
    </div>

    <p><strong>De ce default-ul e MODIFY:</strong> GO și STOP sunt convergențe puternice (≥5/7); orice altă combinație = semnal de dezbatere = MODIFY.</p>

  </section>

  <!-- ══════ TAB: FIȘIERE & MOD ══════ -->
  <section class="tab" id="files">

    <h2>§5 — Hartă fișiere</h2>
    <div class="file-tree">
consilium/<br>
├── SKILL.md <span class="note">              ← secțiunea „Senate mode"</span><br>
├── prompts/<br>
│   ├── generator.md <span class="note">      ← voce core (nu se atinge)</span><br>
│   ├── control.md <span class="note">        ← voce core (nu se atinge)</span><br>
│   ├── conservator.md <span class="note">    ← voce core (nu se atinge)</span><br>
│   └── <span class="new">senators/</span><br>
│       ├── <span class="new">wittgenstein.md · aurelius.md · confucius.md</span><br>
│       └── <span class="new">socrate.md · musk.md · dimon.md · napoleon.md</span><br>
├── scripts/<br>
│   ├── aggregator.py <span class="note">     ← nu se atinge</span><br>
│   ├── <span class="new">senate_synth.py</span>            <span class="note">◄── synth + verdict logic</span><br>
│   ├── <span class="new">senate_synth_fixture.json</span>  <span class="note">◄── smoke test fixture</span><br>
│   └── <span class="new">test_senate_synth.py</span>       <span class="note">◄── 14 smoke tests</span><br>
├── runs/<br>
│   └── <span class="new">senate/</span>                    <span class="note">◄── per-audit bundle (gitignored)</span><br>
│       └── &lt;YYYY-MM-DD_HHMMSS&gt;-&lt;label&gt;.json<br>
└── docs/senate/ <span class="note">          ← acest fișier</span>
    </div>

    <h2 style="margin-top:36px">§6 — Comparație cu alte moduri</h2>
    <table class="data">
      <thead>
        <tr><th>Mod</th><th>Când</th><th>Sub-agenți</th><th>Output</th></tr>
      </thead>
      <tbody>
        <tr><td><code>parallel</code></td><td>schimbări standard</td><td>3 voci independente</td><td><code>runs/*.json</code></td></tr>
        <tr><td><code>dialectic</code></td><td>conf &lt; 0.7 sau risc mediu</td><td>3 × 2 pass</td><td><code>runs/*.json</code></td></tr>
        <tr><td><code>trias</code></td><td>schimbări arhitecturale mari</td><td>9 (3 personalități × 3 voci)</td><td><code>runs/*.json</code></td></tr>
        <tr style="background:rgba(192,132,252,.08)"><td><strong>senate</strong></td><td>modificări la skill însuși (L3 only)</td><td>7 senatori</td><td><code>runs/senate/*.json</code></td></tr>
      </tbody>
    </table>

  </section>

  <!-- ══════ TAB: SELF-IMPROVEMENT ══════ -->
  <section class="tab" id="self-improvement">

    <h2>§7 — Self-improvement loop</h2>
    <p>Senatul se poate evalua pe sine. Înainte de orice modificare la <code>SKILL.md</code> sau la prompt-urile senatorilor, rulezi <code>/consilium senate</code> cu propunerea ta ca input.</p>
    <p>Output-ul merge în <code>runs/senate/</code> (gitignored). Dacă verdictul e GO sau MODIFY cu modify_requests clare, implementezi și comiti. Dacă STOP — revizuiești propunerea.</p>

    <h2 style="margin-top:36px">§8 — Cross-questions (extensie)</h2>
    <p>Opt-in. Multi-round schema: <code>{"rounds": [...]}</code>. Senatorii pot adresa întrebări unii altora; câștigătorul blocajului se determină prin vot majoritar din senatorii rămași.</p>

    <table class="data">
      <thead><tr><th>Legea</th><th>Condiție de activare</th><th>Efect</th></tr></thead>
      <tbody>
        <tr><td>Law 2</td><td><code>rounds</code> prezent în schema</td><td>Cross-questions între senatori (max 4/rundă)</td></tr>
        <tr><td>Law 3</td><td>GO×STOP pair detectat</td><td>Blocaj — cei doi trebuie să se întrebe reciproc; resolution prin vot majoritar</td></tr>
        <tr><td>Law 4</td><td>schimbări de poziție în rundă anterioară</td><td><code>position_changes[]</code> populat + trigger inferat</td></tr>
      </tbody>
    </table>

    <p class="note">Schimbările de poziție (<em>position_changes</em>) sunt <strong>semnalul</strong> că dinamica funcționează. Un Senat care converge mereu fără schimbări e suspect (groupthink structural).</p>

  </section>

  <!-- ══════ TAB: LIMITĂRI & TEST ══════ -->
  <section class="tab" id="limits">

    <h2>§9 — Limitări cunoscute</h2>
    <table class="data">
      <thead><tr><th>Limitare</th><th>Status</th><th>Plan viitor</th></tr></thead>
      <tbody>
        <tr><td>Cross-questions între senatori</td><td>Activ (opt-in multi-round)</td><td>Empirical validation: ≥3 invocări reale</td></tr>
        <tr><td>Blocaj resolution</td><td>Activ (opt-in multi-round)</td><td>Empirical validation după prima activare</td></tr>
        <tr><td>Principle extraction din pattern detection</td><td>Lipsă</td><td>După 30+ runs reale</td></tr>
        <tr><td>Scope-overlap detector între senatori</td><td>Lipsă</td><td>Validare statică în CI dacă există</td></tr>
        <tr><td>Empirical validation Napoleon</td><td>Lipsă</td><td>După 10+ invocări, decide retain vs retire</td></tr>
      </tbody>
    </table>

    <h2 style="margin-top:36px">§10 — Smoke test</h2>
    <p>Două nivele de verificare end-to-end:</p>

    <h3>1. Synth pe fixture</h3>
    <pre class="code-block">cat scripts/senate_synth_fixture.json | python -X utf8 scripts/senate_synth.py</pre>
    <p><strong>Așteptare:</strong> <code>verdict: MODIFY</code>, <code>vote_counts: {GO:3, MODIFY:3, STOP:1}</code>, <code>warnings</code> cu senator dimon silent.</p>

    <h3>2. Suite completă (14 teste)</h3>
    <pre class="code-block">python -X utf8 scripts/test_senate_synth.py</pre>
    <p>Toate 14 trebuie să PASS înainte de orice commit pe <code>senate_synth.py</code> sau <code>prompts/senators/*.md</code>. Cazuri acoperite: verdict GO/MODIFY/STOP/UNREACHABLE, quorum, multi-round position changes, blocaj, collision-safe write.</p>

    <footer>
      <p>
        <strong>Surse:</strong>
        <a href="../../SKILL.md">SKILL.md</a> ·
        <a href="../../scripts/senate_synth.py">senate_synth.py</a> ·
        <a href="../../experiments/New%20phase%20senat/">experiments/New phase senat/</a> ·
        <a href="../architecture.html">docs/architecture.html</a> (main)
      </p>
    </footer>

  </section>

</main>

<script>
  mermaid.initialize({ startOnLoad: true, securityLevel: 'loose',
    theme: 'dark',
    themeVariables: {
      primaryColor: '#21262d', primaryTextColor: '#e5e7eb',
      primaryBorderColor: '#2d3441', lineColor: '#9ca3af',
      secondaryColor: '#11151c', tertiaryColor: '#0f1419',
      edgeLabelBackground: '#11151c'
    }
  });

  (function() {
    var tabs = document.querySelectorAll('nav.tabs button');
    var sections = document.querySelectorAll('section.tab');
    tabs.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var target = btn.getAttribute('data-tab');
        tabs.forEach(function(b) { b.classList.remove('active'); });
        sections.forEach(function(s) { s.classList.remove('active'); });
        btn.classList.add('active');
        var sec = document.getElementById(target);
        if (sec) sec.classList.add('active');
      });
    });
  })();
</script>

</body>
</html>
```

- [ ] **Step 3: Verify in browser**

Open `docs/senate/architecture.html`. All 7 tabs navigate correctly. Mermaid diagrams render in Overview (layers), Dispatch (sequence), Verdict (flowchart). Senator cards display. Tables display.

- [ ] **Step 4: Commit**

```bash
git add docs/senate/architecture.html
git commit -m "feat(senate): redesign architecture.html — tab-based layout + Mermaid diagrams"
```

---

## Task 7: Delete consilium-viz.html + final verification

**Files:**
- Delete: `consilium-viz.html`

- [ ] **Step 1: Verify all content is present in docs/architecture.html**

Open `docs/architecture.html` in browser. Check:
- [ ] Tab "Dialectic" exists and renders sequence + flowchart diagrams
- [ ] Tab "TODO Matrix" exists and renders bubble chart (hover shows tooltip)
- [ ] Tab "Memory" includes Observe→Think→Act→Learn Mermaid diagram
- [ ] Tab "Flow" includes Mermaid overview above step-cards
- [ ] All existing tabs still work (Architecture, Modes, Memory, Patterns, Voices, Files, Git)

- [ ] **Step 2: Delete consilium-viz.html**

```bash
git rm consilium-viz.html
```

- [ ] **Step 3: Final commit**

```bash
git add docs/architecture.html
git commit -m "feat(arch): merge consilium-viz content into architecture.html, delete consilium-viz.html"
```

---

## Self-review

**Spec coverage:**
- ✅ `docs/architecture.html` — Mermaid CDN (Task 1) + Flow overview (Task 2) + Memory O→T→A→L (Task 3) + Dialectic tab (Task 4) + TODO Matrix tab (Task 5)
- ✅ `docs/senate/architecture.html` — full redesign with gold dark theme + tabs + Mermaid (Task 6)
- ✅ `consilium-viz.html` deleted (Task 7)
- ✅ TODO Matrix kept as SVG (Mermaid doesn't support scatter)
- ✅ Patterns tab untouched (Task 7 Step 1 verification)

**Placeholders:** None. All steps include exact HTML/JS/CSS content.

**Type consistency:** `todoMatrixSvg` (id in HTML) ↔ `getElementById('todoMatrixSvg')` (JS) ✅. `todoItems` array ↔ used in `drawTodoMatrix` ✅. `drawTodoMatrix` called on tab switch ✅.
