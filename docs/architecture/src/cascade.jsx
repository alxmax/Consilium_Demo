/* cascade.jsx — 8-component veto cascade + two-layer architecture */

const CASCADE_ROWS = [
  {
    trigger: 'irreversibility_flag: true',
    source: 'con',
    sourceName: 'Conservator',
    outcome: 'BLOCK (hard)',
    outcomeKind: 'block',
    action: 'Ask user for explicit consent before Generator runs.',
  },
  {
    trigger: 'glossary_fail: true',
    source: 'ctl',
    sourceName: 'Control',
    outcome: 'BLOCK (soft)',
    outcomeKind: 'block',
    action: 'Ask user to reformulate with operational terms.',
  },
  {
    trigger: 'disagreements: substantial',
    source: 'ctl',
    sourceName: 'Control',
    outcome: 'REWORK',
    outcomeKind: 'rework',
    action: 'Re-run Generator with clarification context.',
  },
  {
    trigger: 'meta_recommendation: scale_down',
    source: 'con',
    sourceName: 'Conservator',
    outcome: 'ADAPT_SHORT',
    outcomeKind: 'adapt',
    action: 'Short-circuit — skip Generator and Control; emit a trivial-direct report (2-sentence output, confidence 0.85, pipeline_executed: false).',
  },
  {
    trigger: 'meta_recommendation: scale_up',
    source: 'con',
    sourceName: 'Conservator',
    outcome: 'ADAPT_EXTENDED',
    outcomeKind: 'adapt',
    action: 'Warn user, add context before Generator.',
  },
  {
    trigger: '3+ of above simultaneously',
    source: 'agg',
    sourceName: 'Aggregator',
    outcome: 'ESCALATE',
    outcomeKind: 'escalate',
    action: 'Present the trigger table to the user, request decision.',
  },
  {
    trigger: 'none of above',
    source: 'default',
    sourceName: 'default',
    outcome: 'AGGREGATE',
    outcomeKind: 'aggregate',
    action: 'Default path — voices aggregated via conservative_override.',
  },
];

function CascadeSection() {
  return (
    <section className="section section--tinted" id="cascade">
      <div className="container">
        <SectionHead
          num="05"
          eyebrow="Aggregation routing"
          title="Before voting: a seven-outcome safety check."
          lede="Before computing any score, the aggregator runs through a priority-ordered checklist of seven conditions. Each maps to a routing outcome. The first condition that fires determines what happens — BLOCK, REWORK, ADAPT, ESCALATE, or normal AGGREGATE. Most runs reach the last row."
        />

        <div className="tldr">
          <span className="tldr__label">In plain words</span>
          <div>
            <p>Before computing any score, the system asks a few yes/no questions about what the voices said. If any answer is "yes, this looks dangerous," the cascade short-circuits to <strong>BLOCK</strong>, <strong>REWORK</strong>, or <strong>ADAPT</strong>. Otherwise, the default path is normal aggregation.</p>
          </div>
        </div>

        <div className="cascade-grid" role="table" aria-label="Veto cascade triggers">
          <div className="cascade-row cascade-row__head" role="row">
            <div className="cascade-cell" role="columnheader">Trigger</div>
            <div className="cascade-cell" role="columnheader">Source</div>
            <div className="cascade-cell" role="columnheader">Outcome</div>
            <div className="cascade-cell" role="columnheader">Action</div>
          </div>
          {CASCADE_ROWS.slice(0, 3).map((r, i) => (
            <div className="cascade-row" key={i} role="row" style={{ animationDelay: `${i * 60}ms`, animation: 'fade-up 0.5s ease-out backwards' }}>
              <div className="cascade-cell"><code>{r.trigger}</code></div>
              <div className="cascade-cell">
                <SourceChip source={r.source} name={r.sourceName} />
              </div>
              <div className="cascade-cell">
                <span className={`outcome-pill outcome-pill--${r.outcomeKind}`}>{r.outcome}</span>
              </div>
              <div className="cascade-cell" style={{ color: 'var(--ink-2)', fontSize: 13 }}>{r.action}</div>
            </div>
          ))}
        </div>

        <Collapsible label="Show remaining triggers (4 of 7)">
          <div className="cascade-grid" role="table" style={{ marginTop: 0 }}>
            {CASCADE_ROWS.slice(3).map((r, i) => (
              <div className="cascade-row" key={i} role="row">
                <div className="cascade-cell"><code>{r.trigger}</code></div>
                <div className="cascade-cell">
                  <SourceChip source={r.source} name={r.sourceName} />
                </div>
                <div className="cascade-cell">
                  <span className={`outcome-pill outcome-pill--${r.outcomeKind}`}>{r.outcome}</span>
                </div>
                <div className="cascade-cell" style={{ color: 'var(--ink-2)', fontSize: 13 }}>{r.action}</div>
              </div>
            ))}
          </div>
        </Collapsible>

        <div className="note" style={{ marginTop: 24 }}>
          <span className="note__label">Veto budget</span>
          <span>
            Five activations of <code>scale_up</code> or <code>scale_down</code> per month. Past that, soft warning only — the gate softens itself when overused. Once every twenty runs, parallel mode runs silently alongside sequential as an audit; systematic divergence raises the audit frequency to one in five.
          </span>
        </div>

        <div className="note" style={{ marginTop: 16 }}>
          <span className="note__label">Headless invariants</span>
          <span>
            When <code>CLAUDE_HEADLESS=1</code> (set by an external orchestrator that invoked <code>claude -p</code>), four points in the workflow drop user-facing prompts and use documented defaults: stale_pendings/missing_feedback_runs are auto-suppressed at bootstrap, irreversibility_flag does not block (the orchestrator has assumed the stake), retry on low confidence is skipped, and unresolved verdicts log as <code>PEND_HEADLESS</code>.
          </span>
        </div>
      </div>
    </section>
  );
}

function SourceChip({ source, name }) {
  const colorMap = {
    gen: 'var(--gen)',
    ctl: 'var(--ctl)',
    con: 'var(--con)',
    agg: 'var(--ink)',
    default: 'var(--ink-3)',
  };
  return (
    <span className="source-chip">
      <span className="source-chip__dot" style={{ background: colorMap[source] }} />
      {name}
    </span>
  );
}

/* === Two-layer architecture overview === */

function TwoLayerSection() {
  return (
    <section className="section" id="architecture">
      <div className="container">
        <SectionHead
          num="03"
          eyebrow="Architecture"
          title="Two layers, distinct scope."
          lede="Deliberation does the per-question work; aggregation decides what the user actually sees. Same pipeline, two responsibilities."
        />

        <div className="two-layer">
          <div className="two-layer__cell">
            <div className="two-layer__tag">LAYER 1</div>
            <h3 className="two-layer__name">Deliberation</h3>
            <p className="two-layer__desc">
              Runs on every user question. The three voices process the change in sequence (Conservator → Generator → Control) inside a single context, with <code>strip_context.py</code> projecting the Generator's candidates down to id/summary/sketch before Control sees them — minimizing cross-voice contamination.
            </p>
            <div className="two-layer__bits">
              <div className="two-layer__bit">3 voices, run in fixed order</div>
              <div className="two-layer__bit">parallel auto-fires only on critical + irreversible</div>
              <div className="two-layer__bit">silent audit every 20 runs</div>
              <div className="two-layer__bit">no sub-agents by default</div>
            </div>
          </div>

          <div className="two-layer__cell">
            <div className="two-layer__tag">LAYER 2</div>
            <h3 className="two-layer__name">Aggregation</h3>
            <p className="two-layer__desc">
              Synthesizes the three outputs into a single user-facing decision via the 8-component veto cascade. Routes to BLOCK / REWORK / ADAPT_SHORT / ADAPT_EXTENDED / ESCALATE — or runs normal aggregation when no trigger fires.
            </p>
            <div className="two-layer__bits">
              <div className="two-layer__bit">aggregate_sequential() with 8-component cascade</div>
              <div className="two-layer__bit">7 routing outcomes</div>
              <div className="two-layer__bit">veto budget: 5 activations / month</div>
              <div className="two-layer__bit">default scheme: conservative_override</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

window.CascadeSection = CascadeSection;
window.TwoLayerSection = TwoLayerSection;
