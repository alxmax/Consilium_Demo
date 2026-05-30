/* loop.jsx — calibration / feedback loop */

function LoopSection() {
  return (
    <section className="section section--tinted" id="loop">
      <div className="container">
        <SectionHead
          num="10"
          eyebrow="Calibration"
          title="The skill calibrates itself between runs."
          lede="Every deliberation appends an outcome line to FEEDBACK.html. Before the next run, priors.py reads the log and computes soft priors the orchestrator injects at step 0 — so the system's risk intuition tunes itself on real history."
        />

        <div className="loop-cell">
          <LoopDiagram />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginTop: 28 }}>
          <OutcomeChip code="OK" desc="auto-logged, confidence ≥ 0.7" />
          <OutcomeChip code="OVR" desc="user overrode the chosen candidate" />
          <OutcomeChip code="PEND" desc="deferred — retro-closed via stale_pendings" warn />
          <OutcomeChip code="BAD" desc="set manually later if the decision failed" warn />
        </div>
      </div>
    </section>
  );
}

function OutcomeChip({ code, desc, warn }) {
  return (
    <div style={{
      background: 'var(--paper)',
      border: '1px solid var(--rule)',
      borderLeft: `3px solid ${warn ? 'oklch(0.55 0.18 25)' : 'var(--ink)'}`,
      padding: '14px 18px',
      borderRadius: '0 4px 4px 0',
    }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 14, letterSpacing: '0.05em', marginBottom: 4 }}>{code}</div>
      <div style={{ fontSize: 12, color: 'var(--ink-2)' }}>{desc}</div>
    </div>
  );
}

function LoopDiagram() {
  return (
    <svg viewBox="0 0 1000 320" className="diagram">
      <ArrowDefs id="lp" />

      {/* The four stations laid out in a horizontal cycle with a return loop */}
      {[
        { x: 30,  title: 'Deliberation', sub: 'voices · steps 1 → 5', code: '' },
        { x: 280, title: 'Report', sub: 'step 6 · canonical JSON', code: 'build_report.py · validate_report.py' },
        { x: 530, title: 'FEEDBACK.html', sub: 'append-only outcome log', code: 'OK / OVR / PEND / BAD' },
        { x: 780, title: 'Priors', sub: 'soft priors for next run', code: 'priors.py' },
      ].map((s, i) => (
        <g key={i}>
          <rect x={s.x} y={120} width={190} height={90} rx="4" fill="var(--paper)" stroke="var(--rule-2)" />
          <text x={s.x + 14} y={145} style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: 13, fill: 'var(--ink)' }}>{s.title}</text>
          <text x={s.x + 14} y={163} className="d-faint" style={{ fontSize: 10 }}>{s.sub}</text>
          {s.code && (
            <text x={s.x + 14} y={193} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-2)' }}>{s.code}</text>
          )}
        </g>
      ))}

      {/* arrows forward — animated flow */}
      {[220, 470, 720].map((x, i) => (
        <line key={i} x1={x} y1={165} x2={x + 60} y2={165} className="d-arrow d-arrow--flow" markerEnd="url(#lp)" />
      ))}

      {/* G/C/K dots inside Deliberation */}
      <circle cx="60" cy="190" r="5" fill="var(--gen)" />
      <circle cx="78" cy="190" r="5" fill="var(--ctl)" />
      <circle cx="96" cy="190" r="5" fill="var(--con)" />

      {/* Return loop from Priors back to Deliberation (above) */}
      <path d="M 875 120 C 875 50, 125 50, 125 120" className="d-arrow d-arrow--flow-slow" markerEnd="url(#lp)" />
      <text x="500" y="42" textAnchor="middle" className="d-faint" style={{ fontSize: 11 }}>
        injected at step 0 (bootstrap) — next run reads history
      </text>

      {/* Stale pendings side note */}
      <text x="970" y="240" textAnchor="end" className="d-faint" style={{ fontSize: 10 }}>
        stale_pendings (PEND &gt; 2 days) surfaced before next step 1
      </text>

      {/* Pretty side label */}
      <text x="30" y="280" className="d-faint">CLOSED LOOP · ZERO CODE CHANGE</text>
      <text x="30" y="296" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-2)' }}>
        Override rate, veto rate, top keywords and stale pendings inform the next deliberation's priors.
      </text>
    </svg>
  );
}

window.LoopSection = LoopSection;
