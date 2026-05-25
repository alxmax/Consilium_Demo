/* ============== MERMAID + TAB SWITCHING ============== */
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
    var playBtn = document.getElementById('patPlayBtn');
    function syncPlayBtn(target) {
      if (!playBtn) return;
      playBtn.style.display = target === 'internals' ? '' : 'none';
    }
    var banner = document.getElementById('startBanner');
    if (banner && sessionStorage.getItem('consiliumBannerDone')) { banner.classList.add('hidden'); }
    tabs.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var target = btn.getAttribute('data-tab');
        tabs.forEach(function(b) { b.classList.toggle('active', b === btn); });
        sections.forEach(function(s) { s.classList.toggle('active', s.id === target); });
        if (target === 'internals') { window.__patternsRedraw && window.__patternsRedraw(); }
        syncPlayBtn(target);
        if (banner) { banner.classList.add('hidden'); sessionStorage.setItem('consiliumBannerDone','1'); }
      });
    });
    // Initial state: hide Play tour unless Patterns is the active tab on load
    var initialActive = document.querySelector('nav.tabs button.active');
    syncPlayBtn(initialActive ? initialActive.getAttribute('data-tab') : null);
  })();


  /* ============== PATTERNS — flows, highlight, SVG lines ============== */
  (function() {
    var BASE_PATH = ['dev', 'cc-session', 'skill-md', 'mode', 'generator', 'control', 'conservator', 'agg', 'gate', 'output'];

    var FLOWS = [
      {
        id: 'pr-review',
        name: 'Review PR',
        mode: 'Sequential',
        desc: 'Flux default: cele trei voci rulează secvențial în același context — Conservator scorează riscul și setează token budget, Generator propune, Control verifică.',
        path: ['dev', 'cc-session', 'skill-md', 'mode', 'generator', 'control', 'conservator', 'agg', 'gate', 'output'],
        auxNodes: ['scope-gate'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'], ['generator', 'control'], ['control', 'conservator'],
          ['conservator', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> deschide o sesiune Claude Code cu un diff sau o descriere de schimbare.',
          'Skill-ul se activează prin keyword trigger (ex. <i>review PR</i>) și orchestratorul folosește <b>Sequential mode</b> (default).',
          '<b>Conservator-ul</b> scorează riscul și setează token budget; <b>Generator</b> propune alternative; <b>Control</b> le verifică — toate în același context.',
          'Separarea e prin rol-prompt, nu izolare totală (același model, același context). Parallel rămâne doar ca cross-check intern automat.',
          'Aggregator combină sub <code>conservative_override</code>; riscul rămâne sub pragul de veto, deci gate-ul <b>trece</b>.',
          'Se scrie un <code>runs/&lt;id&gt;.json</code> canonic și un sumar cu opțiunea aleasă în consolă.'
        ]
      },
      {
        id: 'refactor-planning',
        name: 'Planificare refactor',
        mode: 'Dialectic',
        desc: 'Vocile răspund unele la altele între runde înainte de a vota — util pentru refactors multi-fișier unde pozițiile evoluează.',
        path: BASE_PATH,
        auxNodes: ['scope-gate', 'dialectic-merge'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'], ['mode', 'control'], ['mode', 'conservator'],
          ['generator', 'control', 'bi'], ['control', 'conservator', 'bi'], ['generator', 'conservator', 'bi'],
          ['generator', 'agg'], ['control', 'agg'], ['conservator', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> descrie scope-ul refactor-ului și constraints.',
          'Skill-ul alege <b>Dialectic mode</b>: vocile rulează în runde și citesc outputs-urile celorlalți între runde.',
          'Runda 1 — Generator-ul propune 2–3 alternative.',
          'Runda 2 — Control-ul critică fiecare alternativă și poate produce un hibrid.',
          'Runda 3 — Conservator-ul scorează riscul rezidual și flag-uiește edits out-of-scope.',
          'Aggregator-ul converge, gate-ul <b>trece</b>, deliberation log salvat în <code>runs/&lt;id&gt;.json</code>.'
        ]
      },
      {
        id: 'risk-assessment',
        name: 'Evaluare de risc',
        mode: 'Sequential — Blind',
        desc: 'Fiecare voce rulează în izolare cu context stripped; previne anchoring-ul pe framing-ul vocii anterioare.',
        path: BASE_PATH,
        auxNodes: ['scope-gate', 'strip-context'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'],
          ['generator', 'control'],
          ['control', 'conservator'],
          ['conservator', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> trimite o schimbare high-risk (ex. migration, security patch).',
          'Skill-ul alege <b>Sequential — Blind mode</b>: doar diff-ul e partajat; outputs-urile vocii anterioare sunt stripped.',
          '<b>Generator-ul</b> rulează primul și propune alternative fără să vadă vreo critică.',
          '<b>Control-ul</b> rulează după, blind la raționamentul Generator-ului — vede doar propunerile rezultate.',
          '<b>Conservator-ul</b> rulează ultimul și scorează risc pe dimensiunile lui (diff size, scope drift, reversibility).',
          'Risk score sub prag de data asta, gate-ul <b>trece</b>, raportul canonic e scris.'
        ]
      },
      {
        id: 'veto-trigger',
        name: 'Trigger veto',
        mode: 'conservative_override',
        desc: 'Subset al PR review unde riscul Conservator-ului trece de prag și gate-ul eșuează — candidate-ul e respins.',
        path: ['dev', 'cc-session', 'skill-md', 'mode', 'generator', 'control', 'conservator', 'agg', 'gate', 'output'],
        auxNodes: ['scope-gate'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'], ['mode', 'control'], ['mode', 'conservator'],
          ['generator', 'agg'], ['control', 'agg'], ['conservator', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        gateFails: true,
        steps: [
          'O deliberare se termină cu voturi mixte de la Generator și Control.',
          'Risk score-ul <b>Conservator-ului</b> e peste pragul de veto configurat (ex. <code>0.80</code>).',
          'Aggregator-ul declanșează path-ul de veto sub <code>conservative_override</code>.',
          'Gate-ul <b>eșuează</b> — candidate-ul e respins; alternativa next-best e aleasă dacă există.',
          'Run-ul e înregistrat în <code>runs/&lt;id&gt;.json</code> cu <code>veto_triggered: true</code> și pragul.',
          'Consola tipărește rationale-ul vetoului ca developer-ul să decidă dacă revizuiește și reia.'
        ]
      },
      {
        id: 'multi-file',
        name: 'Refactor multi-fișier',
        mode: 'Dialectic',
        desc: 'Diff-uri bundled peste mai multe fișiere; vocile evaluează cohesion, scope drift, și risc per-fișier înainte de o decizie unică.',
        path: BASE_PATH,
        auxNodes: ['scope-gate', 'dialectic-merge'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'], ['mode', 'control'], ['mode', 'conservator'],
          ['generator', 'control', 'bi'], ['control', 'conservator', 'bi'],
          ['generator', 'agg'], ['control', 'agg'], ['conservator', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> pasează un bundle de diff-uri legate la skill.',
          'Skill-ul alege <b>Dialectic mode</b> cu prompts conștiente multi-fișier.',
          'Generator-ul ia fiecare fișier pe rând dar propune o singură direcție coerentă.',
          'Control-ul verifică consistența cross-fișier (simboluri partajate, contracte de tip, error paths).',
          'Conservator-ul scorează <i>scope drift</i> per fișier și flag-uiește edits care nu se potrivesc cu goal-ul.',
          'Aggregator-ul emite o singură decizie + un risk breakdown per-fișier; gate-ul <b>trece</b> și bundle-ul e aprobat ca o unitate.'
        ]
      },
      {
        id: 'trias',
        name: 'Deliberare Trias',
        mode: 'Trias',
        desc: 'Trei personalități (Pioneer/Architect/Steward), fiecare rulează o deliberare Sequential proprie ca un singur sub-agent, apoi un vot democratic majoritar tranșează alegerea. Cost: 3× Sequential (3 sub-agenți).',
        path: ['dev', 'cc-session', 'skill-md', 'mode', 'pioneer', 'architect', 'steward', 'agg', 'gate', 'output'],
        auxNodes: ['scope-gate'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'pioneer'], ['mode', 'architect'], ['mode', 'steward'],
          ['pioneer', 'agg'], ['architect', 'agg'], ['steward', 'agg'],
          ['agg', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> opt-in la <b>Trias mode</b> pentru o decizie high-stakes (ex. alegere de arhitectură).',
          'Skill-ul dispatch trei personalități — Pioneer (G-weighted), Architect (C-weighted), Steward (K-weighted).',
          'Fiecare personalitate rulează propria deliberare Sequential (Conservator→Generator→Control) ca un singur sub-agent — 3 sub-agenți în total (nu 9, ca în designul vechi arhivat).',
          'Un vot democratic majoritar e luat peste personalități — 3-0, 2-1, sau 2-0 dă o decizie automată.',
          'Un split 1-1-1 sau o minoritate slabă escaladează run-ul în loc să decidă automat.',
          'Când majoritatea e atinsă, gate-ul <b>trece</b> și raportul canonic înregistrează toate cele trei voturi de personalitate.'
        ]
      },
      {
        id: 'skeptic-challenge',
        name: 'Provocare Skeptic',
        mode: 'Sequential + skeptic_on_chosen',
        desc: 'Flag compozabil peste orice mod de bază. Când confidence ∈ [0.5, 0.7], un Skeptic focal provoacă <code>chosen</code> — primește doar chosen, nu și ceilalți candidați.',
        path: ['dev', 'cc-session', 'skill-md', 'mode', 'generator', 'control', 'conservator', 'agg', 'skeptic', 'gate', 'output'],
        auxNodes: ['scope-gate'],
        edges: [
          ['dev', 'cc-session'], ['cc-session', 'skill-md'], ['skill-md', 'mode'],
          ['mode', 'generator'], ['generator', 'control'], ['control', 'conservator'],
          ['conservator', 'agg'],
          ['agg', 'skeptic'], ['skeptic', 'gate'], ['gate', 'output']
        ],
        steps: [
          '<b>Developer-ul</b> rulează un review obișnuit (<b>Sequential</b>, modul default).',
          'Cele trei voci rulează secvențial; aggregator-ul produce <code>chosen</code> + confidence.',
          'Confidence cade în zona marginală <code>[0.5, 0.7]</code> — orchestratorul activează automat flag-ul <b><code>skeptic_on_chosen</code></b> peste modul de bază.',
          'Un sub-agent focal <b>Skeptic</b> (<code>prompts/voices/skeptic.md</code>) primește <i>doar</i> <code>chosen</code> și <code>success_criterion</code> — fără ceilalți candidați, fără voturile vocilor de bază.',
          'Skeptic-ul produce un challenge focal: advisory by default (logat în <code>deliberation_log</code>); cu <code>--skeptic-can-override</code> poate propune schimbarea alegerii.',
          'Cost: +1 sub-agent Skeptic peste modul de bază (Sequential + flag ≈ 1.33×). Nu se activează dacă confidence ≥ 0.7 sau < 0.5.'
        ]
      }
    ];

    function flowEdges(flow) {
      if (flow.edges) return flow.edges;
      var out = [];
      for (var i = 0; i < flow.path.length - 1; i++) {
        out.push([flow.path[i], flow.path[i + 1]]);
      }
      return out;
    }

    var diagram = document.getElementById('patDiagram');
    var grid    = document.getElementById('patGrid');
    var svg     = document.getElementById('patSvg');
    var flowsBox = document.getElementById('patFlows');
    var stepsList = document.getElementById('patStepsList');
    if (!diagram || !grid || !svg || !flowsBox || !stepsList) return;

    var SVG_NS = 'http://www.w3.org/2000/svg';
    var activeFlow = FLOWS[0].id;

    /* Render flow buttons */
    FLOWS.forEach(function(f) {
      var btn = document.createElement('button');
      btn.className = 'pat-flow' + (f.id === activeFlow ? ' active' : '');
      btn.setAttribute('data-flow', f.id);
      btn.innerHTML =
        '<div class="pf-name">' + f.name + ' <span class="pf-mode">' + f.mode + '</span></div>' +
        '<div class="pf-desc">' + f.desc + '</div>';
      btn.addEventListener('click', function() { setActive(f.id); });
      flowsBox.appendChild(btn);
    });

    function getNodeCenters() {
      var diagRect = diagram.getBoundingClientRect();
      var centers = {};
      diagram.querySelectorAll('.pat-node').forEach(function(n) {
        var r = n.getBoundingClientRect();
        // Skip nodes that are display:none (zero-size). These exist in DOM for
        // alternate flow sets (e.g., Personalities for Trias) but are hidden when
        // the flow doesn't apply, so they should not anchor any edges.
        if (r.width === 0 && r.height === 0) return;
        centers[n.getAttribute('data-node')] = {
          x: r.left - diagRect.left + r.width / 2,
          y: r.top  - diagRect.top  + r.height / 2,
          right:  r.right  - diagRect.left,
          left:   r.left   - diagRect.left,
          top:    r.top    - diagRect.top,
          bottom: r.bottom - diagRect.top,
          width: r.width,
          height: r.height,
          el: n
        };
      });
      return centers;
    }

    /* Union of all edges across flows — used to draw the always-visible base graph. Each flow's edges are either explicit (flow.edges) or derived from consecutive path elements. Edge tuple: [from, to] or [from, to, 'bi']. */
    function edgeKey(e) { return e[0] + '>' + e[1] + (e[2] === 'bi' ? '|bi' : ''); }

    function allConnections() {
      var set = {};
      FLOWS.forEach(function(f) {
        flowEdges(f).forEach(function(e) {
          set[edgeKey(e)] = e;
        });
      });
      return Object.values(set);
    }
    var CONNECTIONS = allConnections();

    function flowConnectionSet(flow) {
      var s = {};
      flowEdges(flow).forEach(function(e) {
        s[edgeKey(e)] = true;
      });
      return s;
    }

    /* Compute the SVG path for an edge between two node positions.
       Three regimes:
         - same column (vertical edge):  route as a J-curve along the right side of the column
         - forward (a.x < b.x):          standard left-to-right S-curve, anchored a.right -> b.left
                                         with optional y offsets at both ends to support fan-in / fan-out
         - backward (a.x > b.x):         anchored a.left -> b.right; path goes right-to-left
       The y-offsets let multiple edges into the same target enter at distinct points
       on the target's left edge, so curves do not pile up and overlap intervening nodes.
    */
    /* Detect whether an edge is vertical-dominant (top-to-bottom flow) or
       horizontal-dominant (left-to-right flow). The layout is now top-to-bottom
       so most edges are vertical, but same-row edges (skill-md -> mode, voice <-> voice
       in Dialectic) are horizontal. */
    function pathBetween(a, b, opts) {
      opts = opts || {};
      var dx = b.x - a.x;
      var dy = b.y - a.y;
      var verticalDominant = Math.abs(dy) > Math.abs(dx);

      if (verticalDominant) {
        // Top-to-bottom (or reversed): anchor source.bottom -> target.top
        var down = dy >= 0;
        var src = down ? a : b;
        var dst = down ? b : a;
        var sx = (down ? (opts.srcOffsetX || 0) : (opts.dstOffsetX || 0));
        var tx = (down ? (opts.dstOffsetX || 0) : (opts.srcOffsetX || 0));
        var x1 = src.x + sx, y1 = src.bottom;
        var x2 = dst.x + tx, y2 = dst.top;
        var amp = Math.max(36, (y2 - y1) * 0.55);
        return {
          d: 'M ' + x1 + ' ' + y1 +
             ' C ' + x1 + ' ' + (y1 + amp) + ', ' +
                     x2 + ' ' + (y2 - amp) + ', ' +
                     x2 + ' ' + y2,
          reversed: !down,
          vertical: true
        };
      }

      // Horizontal: anchor source.right -> target.left
      var forward = dx >= 0;
      var src = forward ? a : b;
      var dst = forward ? b : a;
      var sOff = forward ? (opts.srcOffsetY || 0) : (opts.dstOffsetY || 0);
      var dOff = forward ? (opts.dstOffsetY || 0) : (opts.srcOffsetY || 0);
      var x1 = src.right, y1 = src.y + sOff;
      var x2 = dst.left,  y2 = dst.y + dOff;
      var amp = Math.max(36, (x2 - x1) * 0.55);
      return {
        d: 'M ' + x1 + ' ' + y1 +
           ' C ' + (x1 + amp) + ' ' + y1 + ', ' +
                   (x2 - amp) + ' ' + y2 + ', ' +
                   x2 + ' ' + y2,
        reversed: !forward,
        vertical: false
      };
    }

    /* For each edge in the render set, compute small src/dst offsets so that:
         - vertical edges (top-to-bottom layout): spread along X axis at the node's top/bottom edge
         - horizontal edges: spread along Y axis at the node's left/right edge
       Edges are classified as vertical or horizontal based on geometry, and the
       perpendicular axis is the spread axis. Multiple incoming or outgoing edges
       to the same node are distributed evenly across the node's perpendicular span. */
    function computeEdgeOffsets(edgesToDraw, centers) {
      function isVertical(edge) {
        var a = centers[edge[0]], b = centers[edge[1]];
        if (!a || !b) return false;
        return Math.abs(b.y - a.y) > Math.abs(b.x - a.x);
      }

      // Group edges by (endpoint, axis). Spread is only within a same-axis group.
      var groups = {};
      function add(map, key, edge) {
        map[key] = map[key] || [];
        map[key].push(edge);
      }
      edgesToDraw.forEach(function(edge) {
        var axis = isVertical(edge) ? 'v' : 'h';
        add(groups, 'src|' + edge[0] + '|' + axis, edge);
        add(groups, 'dst|' + edge[1] + '|' + axis, edge);
      });

      // Within each group, sort by the OTHER endpoint's perpendicular-axis position,
      // so the spread comes out in geometric order.
      Object.keys(groups).forEach(function(key) {
        var parts = key.split('|');
        var role = parts[0];      // 'src' or 'dst'
        var axis = parts[2];      // 'v' or 'h'
        var otherIdx = role === 'src' ? 1 : 0;
        groups[key].sort(function(e1, e2) {
          var c1 = centers[e1[otherIdx]], c2 = centers[e2[otherIdx]];
          if (!c1 || !c2) return 0;
          return axis === 'v' ? (c1.x - c2.x) : (c1.y - c2.y);
        });
      });

      function spread(idx, total, span) {
        if (total <= 1) return 0;
        var amp = span * 0.35;
        var t = (idx / (total - 1)) - 0.5;
        return t * 2 * amp;
      }

      var offsets = new Map();
      edgesToDraw.forEach(function(edge) {
        var axis = isVertical(edge) ? 'v' : 'h';
        var srcKey = 'src|' + edge[0] + '|' + axis;
        var dstKey = 'dst|' + edge[1] + '|' + axis;
        var srcGroup = groups[srcKey];
        var dstGroup = groups[dstKey];
        var srcCenter = centers[edge[0]];
        var dstCenter = centers[edge[1]];
        var srcIdx = srcGroup.indexOf(edge);
        var dstIdx = dstGroup.indexOf(edge);

        var off = {};
        if (axis === 'v') {
          // Spread along X axis (perpendicular to vertical flow)
          off.srcOffsetX = (srcGroup.length > 1 && srcCenter)
            ? spread(srcIdx, srcGroup.length, srcCenter.width) : 0;
          off.dstOffsetX = (dstGroup.length > 1 && dstCenter)
            ? spread(dstIdx, dstGroup.length, dstCenter.width) : 0;
        } else {
          // Spread along Y axis (perpendicular to horizontal flow)
          off.srcOffsetY = (srcGroup.length > 1 && srcCenter)
            ? spread(srcIdx, srcGroup.length, srcCenter.height) : 0;
          off.dstOffsetY = (dstGroup.length > 1 && dstCenter)
            ? spread(dstIdx, dstGroup.length, dstCenter.height) : 0;
        }
        offsets.set(edge, off);
      });
      return offsets;
    }

    /* Insert <defs> with arrow markers — called every redraw because svg.innerHTML='' wipes them. */
    function ensureDefs() {
      var defs = document.createElementNS(SVG_NS, 'defs');
      defs.innerHTML =
        '<marker id="pat-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse">' +
          '<path d="M0,0 L10,5 L0,10 z" class="pat-arrow-head"/>' +
        '</marker>' +
        '<marker id="pat-arrow-flow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="14" markerHeight="14" orient="auto" markerUnits="userSpaceOnUse">' +
          '<path d="M0,0 L10,5 L0,10 z" class="pat-arrow-head in-flow"/>' +
        '</marker>' +
        '<marker id="pat-arrow-dim" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse">' +
          '<path d="M0,0 L10,5 L0,10 z" class="pat-arrow-head dim"/>' +
        '</marker>';
      svg.appendChild(defs);
    }

    function redraw() {
      var rect = diagram.getBoundingClientRect();
      // Set data-flow BEFORE measuring node positions — this triggers the CSS
      // swap between Voices and Personalities so we measure the right set.
      diagram.setAttribute('data-flow', activeFlow);

      svg.setAttribute('viewBox', '0 0 ' + rect.width + ' ' + rect.height);
      svg.setAttribute('width', rect.width);
      svg.setAttribute('height', rect.height);

      var centers = getNodeCenters();
      var flow = FLOWS.find(function(f) { return f.id === activeFlow; });
      var inFlow = flowConnectionSet(flow);
      var inFlowNodes = {};
      flow.path.forEach(function(n) { inFlowNodes[n] = true; });
      /* Auxiliary script nodes (scope_gate, strip_context, dialectic_merge, confidence, personalities)
         are not in the edge graph but light up when their mode is active. */
      if (flow.auxNodes) {
        flow.auxNodes.forEach(function(n) { inFlowNodes[n] = true; });
      }

      diagram.querySelectorAll('.pat-node').forEach(function(n) {
        var id = n.getAttribute('data-node');
        n.classList.toggle('in-flow', !!inFlowNodes[id]);
        n.classList.toggle('dim',     !inFlowNodes[id]);
      });

      /* Gate node flips PASS (default green) <-> FAIL (red) based on the active flow. */
      var gateEl = diagram.querySelector('[data-node="gate"]');
      if (gateEl) {
        gateEl.classList.toggle('failing', !!flow.gateFails);
      }

      svg.innerHTML = '';
      ensureDefs();

      // Filter to drawable edges first so offset computation is over the rendered set
      var edgesToDraw = CONNECTIONS.filter(function(edge) {
        var a = centers[edge[0]], b = centers[edge[1]];
        if (!a || !b) return false;
        if (Math.abs(a.x - b.x) < 4 && Math.abs(a.y - b.y) < 4) return false;
        return true;
      });

      var offsets = computeEdgeOffsets(edgesToDraw, centers);

      edgesToDraw.forEach(function(edge) {
        var aId = edge[0], bId = edge[1], bi = edge[2] === 'bi';
        var a = centers[aId], b = centers[bId];
        var off = offsets.get(edge) || { srcOffsetY: 0, dstOffsetY: 0 };

        var path = pathBetween(a, b, off);
        var isInFlow = !!inFlow[edgeKey(edge)];
        var p = document.createElementNS(SVG_NS, 'path');
        p.setAttribute('d', path.d);
        p.setAttribute('class', 'pat-line ' + (isInFlow ? 'in-flow' : 'dim'));

        var markerId = isInFlow ? 'pat-arrow-flow' : 'pat-arrow-dim';
        var arrowUrl = 'url(#' + markerId + ')';

        if (bi) {
          p.setAttribute('marker-start', arrowUrl);
          p.setAttribute('marker-end',   arrowUrl);
        } else if (path.reversed) {
          p.setAttribute('marker-start', arrowUrl);
        } else {
          p.setAttribute('marker-end',   arrowUrl);
        }
        svg.appendChild(p);
      });
    }

    function setActive(id) {
      activeFlow = id;
      flowsBox.querySelectorAll('.pat-flow').forEach(function(b) {
        b.classList.toggle('active', b.getAttribute('data-flow') === id);
      });
      var flow = FLOWS.find(function(f) { return f.id === id; });
      stepsList.innerHTML = flow.steps.map(function(s) { return '<li>' + s + '</li>'; }).join('');
      redraw();
    }

    window.__patternsRedraw = redraw;
    window.addEventListener('resize', function() {
      // Debounce
      clearTimeout(window.__patResizeT);
      window.__patResizeT = setTimeout(redraw, 80);
    });

    /* Fullscreen toggle (applies to the whole document, not just #patterns) */
    var fsBtn = document.getElementById('patFullscreenBtn');
    var fsTarget = document.documentElement;
    function isFullscreen() { return !!(document.fullscreenElement || document.webkitFullscreenElement); }
    function enterFullscreen() {
      if (isFullscreen()) return Promise.resolve();
      var req = fsTarget.requestFullscreen || fsTarget.webkitRequestFullscreen;
      if (!req) return Promise.resolve();
      try {
        var p = req.call(fsTarget);
        return (p && p.then) ? p : Promise.resolve();
      } catch (e) { return Promise.resolve(); }
    }
    function exitFullscreen() {
      if (!isFullscreen()) return;
      var doc = document;
      if (doc.exitFullscreen) doc.exitFullscreen();
      else if (doc.webkitExitFullscreen) doc.webkitExitFullscreen();
    }
    if (fsBtn) {
      fsBtn.addEventListener('click', function() {
        if (isFullscreen()) exitFullscreen();
        else enterFullscreen();
      });
      function onFsChange() {
        var fs = isFullscreen();
        fsBtn.querySelector('.icon').textContent = fs ? '⤣' : '⤢';
        fsBtn.querySelector('.label').textContent = fs ? 'Ieși din ecran complet' : 'Ecran complet';
        setTimeout(redraw, 100);
      }
      document.addEventListener('fullscreenchange', onFsChange);
      document.addEventListener('webkitfullscreenchange', onFsChange);
    }

    /* Auto-tour: cycle through every flow with a slow scroll. Optionally play your
       favourite riff in another tab first (we don't embed audio — copyright).      */
    var playBtn = document.getElementById('patPlayBtn');
    var progress = document.getElementById('patTourProgress');
    var tour = { running: false, flowTimer: null, rafId: null };
    var TOUR_FLOW_MS = 5000;

    function setPlayBtnState(running) {
      if (!playBtn) return;
      var icon = playBtn.querySelector('.icon');
      var label = playBtn.querySelector('.label');
      if (running) {
        icon.textContent = '⏹'; label.textContent = 'Oprește tur';
        playBtn.classList.add('running');
      } else {
        icon.textContent = '▶'; label.textContent = 'Pornește tur';
        playBtn.classList.remove('running');
      }
    }

    function getScroller() {
      // In fullscreen on <html>, the documentElement is still the scroller.
      return document.scrollingElement || document.documentElement;
    }

    function stopTour() {
      tour.running = false;
      if (tour.flowTimer) { clearTimeout(tour.flowTimer); tour.flowTimer = null; }
      if (tour.rafId) { cancelAnimationFrame(tour.rafId); tour.rafId = null; }
      setPlayBtnState(false);
      if (progress) {
        progress.classList.remove('active');
        progress.firstElementChild.style.width = '0%';
      }
    }

    /* Smoothly scroll the document scroller to a target Y position over `duration` ms.
       Returns a promise that resolves when the scroll completes (or the tour is stopped). */
    function smoothScrollTo(targetY, duration) {
      return new Promise(function(resolve) {
        var scroller = getScroller();
        var startY = scroller.scrollTop;
        var maxY = scroller.scrollHeight - scroller.clientHeight;
        var endY = Math.max(0, Math.min(maxY, targetY));
        var startTime = Date.now();
        function tick() {
          if (!tour.running) { resolve(); return; }
          var elapsed = Date.now() - startTime;
          var t = Math.min(1, elapsed / duration);
          // ease-in-out cubic
          var eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
          getScroller().scrollTop = startY + (endY - startY) * eased;
          if (t < 1) {
            tour.rafId = requestAnimationFrame(tick);
          } else {
            resolve();
          }
        }
        tour.rafId = requestAnimationFrame(tick);
      });
    }

    /* Tour timings (ms). Total ≈ 28.2s. */
    var TOUR_TIMINGS = {
      scrollToSchema: 4000,
      pauseAtSchema:  1000,
      perFlow:        3000,  // × 6 flows = 18000
      scrollToBottom: 4000,
      pauseAtBottom:  1200
    };

    function startTour() {
      if (tour.running) return;
      tour.running = true;
      setPlayBtnState(true);
      if (progress) progress.classList.add('active');

      var total = FLOWS.length;
      var totalMs = TOUR_TIMINGS.scrollToSchema + TOUR_TIMINGS.pauseAtSchema +
                    (total * TOUR_TIMINGS.perFlow) + TOUR_TIMINGS.scrollToBottom +
                    TOUR_TIMINGS.pauseAtBottom;
      var startTime;
      var labelEl = playBtn ? playBtn.querySelector('.label') : null;
      function updateProgress() {
        if (!tour.running) return;
        var elapsed = Date.now() - startTime;
        var pct = Math.min(100, (elapsed / totalMs) * 100);
        if (progress) progress.firstElementChild.style.width = pct + '%';
        if (labelEl) {
          var remainingSec = Math.max(0, Math.ceil((totalMs - elapsed) / 1000));
          labelEl.textContent = 'Oprește · ' + remainingSec + 's';
        }
        if (pct < 100) tour.rafId = requestAnimationFrame(updateProgress);
      }

      enterFullscreen().then(function() {
        setTimeout(function() {
          if (!tour.running) return;
          startTime = Date.now();
          tour.rafId = requestAnimationFrame(updateProgress);

          var diagramEl = document.getElementById('patDiagram');
          var scroller = getScroller();
          var diagramTopY = scroller.scrollTop + diagramEl.getBoundingClientRect().top - 60;

          // Phase 1: gentle scroll down to the schema
          smoothScrollTo(diagramTopY, TOUR_TIMINGS.scrollToSchema).then(function() {
            if (!tour.running) return;
            // Phase 1.5: 1-second breathing pause at the schema
            return new Promise(function(r) {
              tour.flowTimer = setTimeout(r, TOUR_TIMINGS.pauseAtSchema);
            });
          }).then(function() {
            if (!tour.running) return;
            // Phase 2: cycle every flow at the schema
            var idx = 0;
            setActive(FLOWS[idx].id);
            return new Promise(function(resolve) {
              function nextFlow() {
                if (!tour.running) { resolve(); return; }
                idx++;
                if (idx >= total) { resolve(); return; }
                setActive(FLOWS[idx].id);
                tour.flowTimer = setTimeout(nextFlow, TOUR_TIMINGS.perFlow);
              }
              tour.flowTimer = setTimeout(nextFlow, TOUR_TIMINGS.perFlow);
            });
          }).then(function() {
            if (!tour.running) return;
            // Phase 3: scroll the rest of the page (Voices bias, Trias sections, Calibration)
            var s = getScroller();
            return smoothScrollTo(s.scrollHeight - s.clientHeight, TOUR_TIMINGS.scrollToBottom);
          }).then(function() {
            if (!tour.running) return;
            // Phase 4: brief pause at the bottom, then auto-stop
            return new Promise(function(r) {
              tour.flowTimer = setTimeout(r, TOUR_TIMINGS.pauseAtBottom);
            });
          }).then(function() {
            if (tour.running) stopTour();
          });
        }, 400);
      });
    }

    if (playBtn) {
      playBtn.addEventListener('click', function() {
        if (tour.running) stopTour();
        else startTour();
      });
      // Stop tour if user manually exits fullscreen
      document.addEventListener('fullscreenchange', function() {
        if (!isFullscreen() && tour.running) stopTour();
      });
    }

    // Initial render
    setActive(activeFlow);
    // Re-draw after fonts and reflow settle
    setTimeout(redraw, 50);
    setTimeout(redraw, 250);
  })();
