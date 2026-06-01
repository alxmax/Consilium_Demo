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

        <h3 className="h-sub" style={{ marginTop: 44, fontSize: 20 }}>What "calibration" actually means here</h3>
        <p className="body-prose" style={{ color: 'var(--ink-2)', marginBottom: 14, maxWidth: 780 }}>
          Nothing is re-trained — there are no model weights to update. Calibration here is bookkeeping: each run leaves a typed trace on disk, and <code>priors.py</code> distils the accumulated traces into a few soft signals injected at the next run's bootstrap (step 0). The signals <strong>nudge attention and surface unfinished business — they never override a voice or change a score</strong>. It is a slow instrument: a single run barely moves anything; the patterns only become legible across dozens of runs.
        </p>

        <h3 className="h-sub" style={{ marginTop: 24, fontSize: 16 }}>The signals priors.py computes</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginTop: 12 }}>
          {[
            { k: 'override_rate', v: 'how often the human overrode the chosen answer — a standing humility signal on the aggregator' },
            { k: 'veto_rate', v: 'how often Conservator vetoed every candidate — flags task types where the skill keeps stalling' },
            { k: 'recurring keywords', v: 'task labels that keep reappearing, so a repeat decision can reuse a prior authoritative run (passthrough)' },
            { k: 'stale_pendings', v: 'PEND rows older than 2 days — the next run pauses to ask you to close them before deliberating' },
            { k: 'weighted_bad_rate', v: 'BAD outcomes, with production-confirmed ones (mark_outcome.py) weighted 2× over a subjective first impression' },
            { k: 'pend_pressure', v: 'share of recent runs left unresolved — a soft alert, never a block' },
          ].map((s) => (
            <div key={s.k} style={{ padding: '12px 16px', border: '1px solid var(--rule)', borderRadius: 4, background: 'var(--paper)' }}>
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--ink)', fontWeight: 600 }}>{s.k}</code>
              <div style={{ fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5, marginTop: 4 }}>{s.v}</div>
            </div>
          ))}
        </div>

        <div className="note" style={{ marginTop: 24 }}>
          <span className="note__label">Confidence floors — the per-mode self-check</span>
          <span>
            The other half of calibration runs <em>inside</em> a single deliberation. Each mode has a confidence floor it is expected to clear — <strong>Sequential 0.70 · Dialectic 0.75 · Trias 0.80</strong>. A run that lands below its floor is logged <code>WEAK</code>: a recorded signal that the mode didn't earn its cost on that task. No single WEAK run changes behaviour; the value is the accumulated rate, which becomes meaningful after ~10 runs per mode and tells you whether a pricier mode is actually buying confidence.
          </span>
        </div>

        <div className="note" style={{ marginTop: 16 }}>
          <span className="note__label">Why the loop closes on disk, not in a model</span>
          <span>
            The whole loop is files: <code>.consilium/runs/*.json</code> (one episodic record per run) and <code>.consilium/FEEDBACK.html</code> (one outcome row per use). <code>priors.py</code> reads both at the next bootstrap — that read is the closing edge. Keeping it on disk is deliberate: the trail is inspectable, diffable, and survives across sessions without any training step or external store.
          </span>
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
